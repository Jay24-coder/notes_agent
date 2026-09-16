# Submission note

Given more time, I would add automated retrieval/conflict regression tests on the provided `dump/`, tune vector distance thresholds with labeled Q&A pairs, and improve conflict detection with structured fact extraction instead of a single LLM pass. I would also add an optional richer web search provider (e.g. Tavily) behind configuration.

Trade-offs: the prototype uses a single Typesense collection and LLM-json curator for speed; conflict and relatedness quality depend on embedding recall and prompt discipline rather than a dedicated knowledge graph. Out-of-coverage defaults to a plain “not covered” message so the demo stays reliable without extra API keys, with `--web-search` as an explicit, labeled fallback.
