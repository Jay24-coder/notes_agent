from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from itw.config import Settings
from itw.errors import ItwError


@dataclass(frozen=True)
class ConflictLink:
    note_id: str
    rationale: str


@dataclass(frozen=True)
class CuratorResult:
    tags: list[str]
    related_ids: list[str]
    conflicts: list[ConflictLink]


def _format_candidates(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "(no existing notes in the knowledge base yet)"
    lines: list[str] = []
    for doc in candidates:
        lines.append(
            f"- id={doc.get('id')} path={doc.get('source_path')}\n"
            f"  content: {(doc.get('content') or '')[:500]}"
        )
    return "\n".join(lines)


def run_curator(
    settings: Settings,
    note_content: str,
    note_id: str,
    candidates: list[dict[str, Any]],
) -> CuratorResult:
    client = OpenAI(api_key=settings.openai_api_key)
    system = (
        "You organize personal notes into a knowledge base. "
        "Return ONLY valid JSON with keys: tags (string array), related_ids (string array of "
        "candidate note ids), conflicts (array of objects with note_id and rationale). "
        "Choose tags from the note content only — do not use a fixed taxonomy. "
        "Link related_ids only when content is genuinely related. "
        "Record conflicts only for factual contradictions with existing notes, not mere differences of opinion tone."
    )
    user = (
        f"New note id: {note_id}\n\n"
        f"New note content:\n{note_content}\n\n"
        f"Candidate existing notes:\n{_format_candidates(candidates)}"
    )
    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except Exception as exc:  # noqa: BLE001
        raise ItwError(f"OpenAI curator request failed: {exc}") from exc

    raw = (response.choices[0].message.content or "").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ItwError("Curator returned invalid JSON.") from None

    tags = [str(t) for t in data.get("tags", []) if str(t).strip()]
    related_ids = [
        str(r)
        for r in data.get("related_ids", [])
        if str(r).strip() and str(r) != note_id
    ]
    conflicts: list[ConflictLink] = []
    for item in data.get("conflicts", []):
        if not isinstance(item, dict):
            continue
        cid = str(item.get("note_id", "")).strip()
        if not cid or cid == note_id:
            continue
        rationale = str(item.get("rationale", "")).strip() or "Conflicting facts detected."
        conflicts.append(ConflictLink(note_id=cid, rationale=rationale))

    return CuratorResult(tags=tags, related_ids=related_ids, conflicts=conflicts)
