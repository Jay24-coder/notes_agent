from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from itw.config import Settings
from itw.curator import CuratorResult, run_curator
from itw.embeddings import embed_text
from itw.errors import ItwError
from itw.notes import RawNote, new_created_at, read_note_file
from itw.typesense_store import (
    ensure_collection,
    get_note,
    merge_peer_links,
    upsert_note,
    vector_search,
)


@dataclass(frozen=True)
class IngestSummary:
    note: RawNote
    tags: list[str]
    related_ids: list[str]
    conflict_ids: list[str]
    conflict_details: dict[str, str]


def ingest_note_file(settings: Settings, path: Path) -> IngestSummary:
    logger.info("Ingest start path={}", path)
    ensure_collection(settings)
    note = read_note_file(path)
    logger.debug("Read note id={} title={!r} chars={}", note.note_id, note.title, len(note.content))
    embedding = embed_text(settings, note.content)
    candidates = vector_search(
        settings, embedding, k=8, exclude_id=note.note_id
    )
    logger.debug("Ingest candidates={} for note_id={}", len(candidates), note.note_id)
    curator: CuratorResult = run_curator(
        settings, note.content, note.note_id, candidates
    )

    conflict_ids = [c.note_id for c in curator.conflicts]
    conflict_details = {c.note_id: c.rationale for c in curator.conflicts}

    existing_doc = get_note(settings, note.note_id)
    created_at = (
        int(existing_doc.get("created_at"))
        if existing_doc and existing_doc.get("created_at") is not None
        else new_created_at()
    )

    document = {
        "id": note.note_id,
        "source_path": note.source_path,
        "title": note.title,
        "content": note.content,
        "tags": curator.tags,
        "related_ids": curator.related_ids,
        "conflict_ids": conflict_ids,
        "conflict_details": json.dumps(conflict_details),
        "created_at": created_at,
        "embedding": embedding,
    }
    upsert_note(settings, document)

    for related_id in curator.related_ids:
        merge_peer_links(settings, related_id, add_related=note.note_id)
    for conflict in curator.conflicts:
        merge_peer_links(
            settings,
            conflict.note_id,
            add_conflict=note.note_id,
            conflict_rationale=conflict.rationale,
        )

    logger.info(
        "Ingest done id={} tags={} related={} conflicts={}",
        note.note_id,
        len(curator.tags),
        len(curator.related_ids),
        len(conflict_ids),
    )
    return IngestSummary(
        note=note,
        tags=curator.tags,
        related_ids=curator.related_ids,
        conflict_ids=conflict_ids,
        conflict_details=conflict_details,
    )


def ingest_directory(settings: Settings, directory: Path) -> tuple[list[IngestSummary], list[str]]:
    if not directory.is_dir():
        raise ItwError(f"Directory not found: {directory}")

    paths = sorted(p for p in directory.iterdir() if p.is_file() and not p.name.startswith("."))
    if not paths:
        raise ItwError(f"No note files found in {directory}")

    logger.info("Ingest directory={} files={}", directory, len(paths))
    successes: list[IngestSummary] = []
    failures: list[str] = []
    for path in paths:
        try:
            successes.append(ingest_note_file(settings, path))
        except ItwError as exc:
            logger.error("Ingest failed for {}: {}", path.name, exc.message)
            failures.append(f"{path.name}: {exc.message}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected ingest failure for {}", path.name)
            failures.append(f"{path.name}: {exc}")

    logger.info(
        "Ingest directory done successes={} failures={}",
        len(successes),
        len(failures),
    )
    return successes, failures


def format_ingest_summary(summary: IngestSummary) -> str:
    lines = [
        f"Ingested: {summary.note.source_path}",
        f"  id: {summary.note.note_id}",
        f"  tags: {', '.join(summary.tags) if summary.tags else '(none)'}",
        f"  related: {', '.join(summary.related_ids) if summary.related_ids else '(none)'}",
    ]
    if summary.conflict_ids:
        lines.append(f"  conflicts: {', '.join(summary.conflict_ids)}")
        for cid, rationale in summary.conflict_details.items():
            lines.append(f"    - {cid}: {rationale}")
    else:
        lines.append("  conflicts: (none)")
    return "\n".join(lines)
