from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from loguru import logger

from itw.config import Settings
from itw.embeddings import embed_text
from itw.errors import ItwError
from itw.typesense_store import ensure_collection, vector_search
from itw.web_search import live_web_search


@dataclass(frozen=True)
class AskResult:
    answer: str
    citations: list[str]
    used_web_search: bool
    not_covered: bool


def _collect_conflicts(notes: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Return (note_a, note_b, rationale) conflict pairs among retrieved notes."""
    id_set = {n.get("id") for n in notes}
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str, str]] = []

    for note in notes:
        nid = note.get("id")
        for cid in note.get("conflict_ids") or []:
            if cid in id_set and nid:
                key = tuple(sorted((nid, cid)))
                if key in seen:
                    continue
                seen.add(key)
                details_raw = note.get("conflict_details") or "{}"
                try:
                    details = json.loads(details_raw)
                except json.JSONDecodeError:
                    details = {}
                rationale = details.get(cid) or "Recorded conflict between these notes."
                pairs.append((nid, cid, rationale))
    return pairs


def _format_notes_for_prompt(notes: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for note in notes:
        blocks.append(
            f"NOTE id={note.get('id')}\n"
            f"path={note.get('source_path')}\n"
            f"tags={note.get('tags')}\n"
            f"content:\n{note.get('content')}\n"
        )
    return "\n---\n".join(blocks)


def _not_covered_search_failed_message() -> str:
    return (
        "This question is not covered by your notes, and live web search "
        "did not return a result."
    )


def _try_live_web_search(settings: Settings, question: str) -> AskResult:
    if not settings.tavily_api_key.strip():
        raise ItwError(
            "TAVILY_API_KEY is not set. Add it to .env when using --web-search."
        )
    logger.info("Coverage decision: not covered → live web search")
    try:
        search_result = live_web_search(question, tavily_api_key=settings.tavily_api_key)
    except ItwError:
        logger.warning("Live web search failed; returning not-covered message")
        return AskResult(
            answer=_not_covered_search_failed_message(),
            citations=[],
            used_web_search=False,
            not_covered=True,
        )
    return AskResult(
        answer=f"SOURCE: LIVE WEB SEARCH\n\n{search_result.body}",
        citations=list(search_result.source_urls),
        used_web_search=True,
        not_covered=False,
    )


def ask_question(
    settings: Settings,
    question: str,
    *,
    use_web_search: bool = False,
) -> AskResult:
    logger.info("Ask start use_web_search={}", use_web_search)
    ensure_collection(settings)
    try:
        query_embedding = embed_text(settings, question)
        hits = vector_search(settings, query_embedding, k=8)
    except ItwError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Retrieval failed")
        raise ItwError(f"Retrieval failed: {exc}") from exc

    logger.debug(
        "Ask retrieval hits={} distances={}",
        len(hits),
        [h.get("_vector_distance") for h in hits],
    )

    if not hits:
        logger.info("Coverage decision: not covered (no hits)")
        if use_web_search:
            return _try_live_web_search(settings, question)
        return AskResult(
            answer="This question is not covered by your notes.",
            citations=[],
            used_web_search=False,
            not_covered=True,
        )

    best_distance = hits[0].get("_vector_distance")
    if best_distance is not None and best_distance > settings.retrieval_max_vector_distance:
        logger.info(
            "Coverage decision: not covered (best_distance={} > max={})",
            best_distance,
            settings.retrieval_max_vector_distance,
        )
        if use_web_search:
            return _try_live_web_search(settings, question)
        return AskResult(
            answer="This question is not covered by your notes.",
            citations=[],
            used_web_search=False,
            not_covered=True,
        )

    logger.info(
        "Coverage decision: covered hits={} best_distance={}",
        len(hits),
        best_distance,
    )
    conflict_pairs = _collect_conflicts(hits)
    if conflict_pairs:
        logger.debug("Ask conflict pairs={}", len(conflict_pairs))
    client = OpenAI(api_key=settings.openai_api_key)

    conflict_block = ""
    if conflict_pairs:
        lines = ["Recorded conflicts among retrieved notes:"]
        for a, b, rationale in conflict_pairs:
            lines.append(f"- {a} vs {b}: {rationale}")
        conflict_block = "\n".join(lines) + "\n\n"

    system = (
        "You answer questions using ONLY the provided note excerpts. "
        "Always cite source paths in a final 'Citations:' section. "
        "If notes conflict, present BOTH sides explicitly and ask which version is current "
        "or state which you trust (prefer the note with the later created_at) and why. "
        "Do not invent facts not present in the notes."
    )
    user = (
        f"Question: {question}\n\n"
        f"{conflict_block}"
        f"Retrieved notes:\n{_format_notes_for_prompt(hits)}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("OpenAI answer request failed")
        raise ItwError(f"OpenAI answer request failed: {exc}") from exc

    answer = (response.choices[0].message.content or "").strip()
    citations = [str(n.get("source_path")) for n in hits if n.get("source_path")]

    if conflict_pairs and "conflict" not in answer.lower():
        extra = "\n\nConflict notice: Retrieved notes contain recorded contradictions. "
        extra += conflict_pairs[0][2]
        extra += " Please confirm which note is current."
        answer += extra

    if "Citations:" not in answer:
        answer += "\n\nCitations:\n" + "\n".join(f"- {c}" for c in citations)

    logger.info(
        "Ask complete covered=True citations={} answer_chars={}",
        len(citations),
        len(answer),
    )
    return AskResult(
        answer=answer,
        citations=citations,
        used_web_search=False,
        not_covered=False,
    )
