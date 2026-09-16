# Architecture

## Current (local prototype)

```
┌─────────────┐     ingest / ask      ┌──────────────────┐
│  itw CLI    │ ────────────────────► │  OpenAI API      │
│  (Click)    │   embeddings + chat   │  embeddings+chat │
└──────┬──────┘                       └──────────────────┘
       │
       │ upsert / vector_query
       ▼
┌──────────────────┐
│ Typesense        │  Docker volume `typesense-data`
│ collection notes │  fields: content, tags, related_ids,
└──────────────────┘  conflict_ids, embedding (1536-d)
```

### Ingest (Curator)

1. Read raw note file; stable `id` from resolved source path hash.
2. Embed note with `text-embedding-3-small`.
3. Vector-search existing notes for candidates.
4. LLM proposes content-based tags, related ids, and factual conflicts.
5. Upsert document; bidirectionally update peer `related_ids` / `conflict_ids`.

### Query (Q&A)

1. Embed the question.
2. Typesense vector search (top-k); relevance gate via `RETRIEVAL_MAX_VECTOR_DISTANCE`.
3. If not covered: plain message or optional DuckDuckGo instant answers (`SOURCE: LIVE WEB SEARCH`).
4. Else LLM answers from retrieved excerpts only; citations required; conflicts surfaced from stored metadata and prompt instructions.

### Persistence

Typesense data directory is mounted to a Docker named volume so separate CLI runs see the same index.

## Production-scale (sketch)

- **Ingest:** Async workers (queue per user), idempotent upserts, embedding cache, batch embedding API.
- **Search:** Typesense cluster or managed search; separate metadata graph DB for links/conflicts if relationships grow complex.
- **Quality:** Retrieval eval harness, human-in-the-loop conflict resolution, re-ranking.
- **Security:** Per-tenant collections, encryption at rest, secret management, rate limits on OpenAI.
- **Product:** API + UI, audit log of ingest/answer provenance, optional connectors (email, Notion).
