# Notes Ingestion & Recall Agent

Local prototype that ingests raw text notes into a persistent knowledge base (Typesense + OpenAI embeddings) and answers natural-language questions with citations and explicit conflict surfacing.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker (for Typesense)
- OpenAI API key

## Setup

1. Install dependencies:

```bash
uv sync
```

1. Copy environment template and set your OpenAI key:

```bash
cp env.example .env
# Edit .env — set OPENAI_API_KEY
```

Default Typesense settings match `docker-compose.yml` (`TYPESENSE_API_KEY=xyz`, port `8108`).

1. Start Typesense:

```bash
docker compose up -d
```



## Usage

Ingest one note:

```bash
uv run itw ingest path/to/note.txt
```

Ingest all files in `dump/` (provided sample notes):

```bash
uv run itw ingest-dump dump
```

Ask a question:

```bash
uv run itw ask "What did we decide about the API deadline?"
```

Out-of-coverage with optional labeled live web search:

```bash
uv run itw ask "What is the capital of France?" --web-search
```



## Demo checklist

1. Ingest `dump/` (or `fixtures/demo_notes` for a minimal local test set).
2. Stop and restart Typesense / CLI — notes remain queryable (persistent volume).
3. Ask a question covered by a note — answer includes citations.
4. Ask about the conflicting pair — both sides surfaced.
5. Ask something not in the KB — plain not covered, or `--web-search` with clear labeling.



## Troubleshooting


| Issue                       | Fix                                                |
| --------------------------- | -------------------------------------------------- |
| `OPENAI_API_KEY is not set` | Create `.env` from `env.example`                   |
| Typesense connection errors | Run `docker compose up -d` and check port 8108     |
| Empty `dump/`               | Use task-provided `dump/` or `fixtures/demo_notes` |




## Documentation

- Architecture: [docs/architecture.md](docs/architecture.md)
- Submission note: [docs/submission_note.md](docs/submission_note.md)
- Requirements traceability: [docs/problem_understanding.md](docs/problem_understanding.md)

