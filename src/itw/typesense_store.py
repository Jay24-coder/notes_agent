from __future__ import annotations

import json
from typing import Any

import typesense
from loguru import logger

from itw.config import EMBEDDING_DIMENSION, Settings
from itw.errors import ItwError


def _client(settings: Settings) -> typesense.Client:
    return typesense.Client(
        {
            "nodes": [
                {
                    "host": settings.typesense_host,
                    "port": settings.typesense_port,
                    "protocol": settings.typesense_protocol,
                }
            ],
            "api_key": settings.typesense_api_key,
            "connection_timeout_seconds": 10,
        }
    )


def ensure_collection(settings: Settings) -> None:
    client = _client(settings)
    name = settings.typesense_collection
    try:
        client.collections[name].retrieve()
        logger.info("Typesense collection '{}' already exists", name)
        return
    except typesense.exceptions.ObjectNotFound:
        logger.info("Typesense collection '{}' not found; creating", name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not reach Typesense")
        raise ItwError(f"Could not reach Typesense at {settings.typesense_host}:{settings.typesense_port}: {exc}") from exc

    schema = {
        "name": name,
        "fields": [
            {"name": "source_path", "type": "string"},
            {"name": "title", "type": "string"},
            {"name": "content", "type": "string"},
            {"name": "tags", "type": "string[]", "facet": True},
            {"name": "related_ids", "type": "string[]"},
            {"name": "conflict_ids", "type": "string[]"},
            {"name": "conflict_details", "type": "string", "optional": True},
            {"name": "created_at", "type": "int64"},
            {
                "name": "embedding",
                "type": "float[]",
                "num_dim": EMBEDDING_DIMENSION,
            },
        ],
    }
    try:
        client.collections.create(schema)
        logger.info("Created Typesense collection '{}'", name)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create Typesense collection")
        raise ItwError(f"Failed to create Typesense collection '{name}': {exc}") from exc


def upsert_note(settings: Settings, document: dict[str, Any]) -> None:
    client = _client(settings)
    note_id = document.get("id")
    try:
        client.collections[settings.typesense_collection].documents.upsert(document)
        logger.info("Upserted note id={}", note_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Typesense upsert failed for id={}", note_id)
        raise ItwError(f"Typesense upsert failed: {exc}") from exc


def get_note(settings: Settings, note_id: str) -> dict[str, Any] | None:
    client = _client(settings)
    try:
        doc = client.collections[settings.typesense_collection].documents[note_id].retrieve()
        logger.debug("Retrieved note id={}", note_id)
        return doc
    except typesense.exceptions.ObjectNotFound:
        logger.debug("Note id={} not found", note_id)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Typesense retrieve failed for id={}", note_id)
        raise ItwError(f"Typesense retrieve failed: {exc}") from exc


def _vector_query_param(embedding: list[float], k: int) -> str:
    vec = ",".join(str(v) for v in embedding)
    return f"embedding:([{vec}], k:{k})"


def vector_search(
    settings: Settings,
    embedding: list[float],
    k: int = 8,
    exclude_id: str | None = None,
) -> list[dict[str, Any]]:
    client = _client(settings)
    search: dict[str, Any] = {
        "collection": settings.typesense_collection,
        "q": "*",
        "vector_query": _vector_query_param(embedding, k + (1 if exclude_id else 0)),
        "exclude_fields": "embedding",
    }
    logger.debug(
        "Vector search k={} exclude_id={} max_distance={}",
        k,
        exclude_id,
        settings.retrieval_max_vector_distance,
    )
    try:
        multi = client.multi_search.perform({"searches": [search]})
        results = multi.get("results") or []
        if not results:
            logger.debug("Vector search returned no result blocks")
            return []
        result = results[0]
    except Exception as exc:  # noqa: BLE001
        logger.exception("Typesense vector search failed")
        raise ItwError(f"Typesense vector search failed: {exc}") from exc

    hits: list[dict[str, Any]] = []
    for hit in result.get("hits", []):
        doc = hit.get("document", {})
        if exclude_id and doc.get("id") == exclude_id:
            continue
        doc["_vector_distance"] = hit.get("vector_distance")
        hits.append(doc)
        if len(hits) >= k:
            break
    logger.debug(
        "Vector search hits={} ids={}",
        len(hits),
        [h.get("id") for h in hits],
    )
    return hits


def merge_peer_links(
    settings: Settings,
    peer_id: str,
    *,
    add_related: str | None = None,
    add_conflict: str | None = None,
    conflict_rationale: str | None = None,
) -> None:
    peer = get_note(settings, peer_id)
    if not peer:
        logger.debug("Skip peer link merge; peer id={} missing", peer_id)
        return

    related = list(peer.get("related_ids") or [])
    conflicts = list(peer.get("conflict_ids") or [])
    details_raw = peer.get("conflict_details") or "{}"
    try:
        details: dict[str, str] = json.loads(details_raw)
    except json.JSONDecodeError:
        details = {}

    if add_related and add_related not in related:
        related.append(add_related)
    if add_conflict and add_conflict not in conflicts:
        conflicts.append(add_conflict)
        if conflict_rationale:
            details[add_conflict] = conflict_rationale

    peer["related_ids"] = related
    peer["conflict_ids"] = conflicts
    peer["conflict_details"] = json.dumps(details)
    logger.debug(
        "Merging peer links peer={} add_related={} add_conflict={}",
        peer_id,
        add_related,
        add_conflict,
    )
    upsert_note(settings, peer)
