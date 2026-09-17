# Submission note

Given more time, I would add automated retrieval/conflict regression tests on the provided `dump/`, tune vector distance thresholds with labeled Q&A pairs, and improve conflict detection with structured fact extraction instead of a single LLM pass.

Trade-offs: the prototype uses a single Typesense collection and LLM-json curator for speed; conflict and relatedness quality depend on embedding recall and prompt discipline rather than a dedicated knowledge graph. Out-of-coverage defaults to a plain “not covered” message so the demo stays reliable without a Tavily key; `--web-search` uses Tavily with explicit labeling so external answers are never presented as personal notes.
