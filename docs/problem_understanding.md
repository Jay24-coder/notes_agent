# Notes Ingestion & Recall Agent — Problem Understanding

**Source:** `problem_statement/Notes Ingestion & Recall Agent Task.pdf`  
**Purpose of this document:** Persistent source of truth for requirements while implementing. Distinguishes **stated facts** from **assumptions / interpretations**. Avoids implementation decisions unless the problem statement specifies them.

**Legend**


| Marker           | Meaning                                                               |
| ---------------- | --------------------------------------------------------------------- |
| **[FACT]**       | Explicitly stated in the problem statement                            |
| **[ASSUMPTION]** | Reasonable inference; not explicitly stated — revisit if contradicted |
| **[OPEN]**       | Ambiguity or missing detail that needs a decision later               |


---



## 1. Problem overview and objective



### Overview **[FACT]**

Notes, article snippets, and meeting takeaways accumulate in an unorganized “dump” over time and become hard to search or reuse.

### Objective **[FACT]**

Build an **agent** that:

1. Takes in new **raw notes**.
2. **Organizes** them into a **personal knowledge base** without a human sorting them by hand.
3. Answers **natural-language questions** against everything ingested so far.
4. Tells the user **where an answer actually came from** (citations / provenance).



### Submission format **[FACT]**


| Field      | Value                                          |
| ---------- | ---------------------------------------------- |
| Format     | Local working prototype (screen-recorded demo) |
| Submission | Git repository + screen recording              |




### Effort / timeline **[FACT]**

- Expected effort: approximately **4 hours** of focused work.
- Submission window: within **2 days** from when the task is shared.



### What happens after submission **[FACT]**

A review call will be scheduled to walk through architecture, key decisions, and a live demo.

---



## 2. Business requirements

These capture the *why* / product intent, derived from the problem narrative.


| Requirement                                                  | Type       | Notes                                         |
| ------------------------------------------------------------ | ---------- | --------------------------------------------- |
| Reduce manual organization of personal notes                 | **[FACT]** | Agent organizes without human sorting         |
| Make accumulated notes searchable via natural language       | **[FACT]** | Q&A over ingested content                     |
| Preserve trust via provenance                                | **[FACT]** | Answers must cite source notes                |
| Surface contradictions instead of hiding them                | **[FACT]** | Conflicts must be explicit at query time      |
| Avoid presenting external info as personal knowledge         | **[FACT]** | Live search (if used) must be clearly labeled |
| Demoable local prototype, not necessarily production service | **[FACT]** | Format is local working prototype + recording |


**[ASSUMPTION]** The primary evaluation criteria are correctness of the end-to-end demo flows (ingest, cite, conflict, out-of-coverage), not UI polish or production deployment.

---



## 3. Functional requirements

Two connected pieces must work together **end-to-end** **[FACT]**.

### 3.1 Curator (ingestion)

Given **one new raw note** (a short text file: quick thought, pasted article excerpt, or meeting takeaways) **[FACT]**, the agent must:


| ID  | Requirement                                                                                                                        | Type       |
| --- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| C1  | **Store** the note in a **persistent** knowledge base                                                                              | **[FACT]** |
| C1a | Persistence must survive **separate runs** of the program (not only in-memory for one session)                                     | **[FACT]** |
| C1b | Any local vector store / embedding index is acceptable                                                                             | **[FACT]** |
| C2  | **Decide how to tag/categorize** the note based on its **actual content**                                                          | **[FACT]** |
| C2a | Tagging/categorization must **not** be a fixed rule keyed to file type                                                             | **[FACT]** |
| C2b | Must **not** use a fixed tag taxonomy hardcoded in advance                                                                         | **[FACT]** |
| C3  | Where relevant, **connect** the note to **related existing notes** based on content                                                | **[FACT]** |
| C4  | **Detect** when a new note appears to **conflict** with something already in the KB (e.g. a fact that contradicts an earlier note) | **[FACT]** |
| C5  | **Record** that conflict relationship                                                                                              | **[FACT]** |
| C6  | Conflict relationships must be **surfaced later at query time**, not silently dropped                                              | **[FACT]** |


**[ASSUMPTION]** “Connect … related existing notes” implies some form of explicit relatedness/link metadata stored alongside or within the KB, not only incidental similarity during retrieval.

**[OPEN]** Exact representation of tags, categories, and links is not specified (names, graph edges, metadata fields, etc.).

**[OPEN]** How many related notes to link, and the threshold for “related,” are not specified.

**[OPEN]** Conflict detection criteria (factual contradiction vs. opinion difference vs. outdated info) are only exemplified (“a fact that contradicts an earlier note”).

### 3.2 Q&A over the knowledge base

Given a **natural-language question** **[FACT]**, the agent must:


| ID  | Requirement                                                                               | Type                         |
| --- | ----------------------------------------------------------------------------------------- | ---------------------------- |
| Q1  | **Retrieve relevant notes** over the knowledge base                                       | **[FACT]**                   |
| Q1a | Retrieval must **not** be keyword/substring matching alone                                | **[FACT]**                   |
| Q1b | Must **not** stuff the **entire** knowledge base into one prompt                          | **[FACT]**                   |
| Q2  | Answer using **only** what’s actually retrieved                                           | **[FACT]**                   |
| Q3  | **Cite** which note(s) the answer is based on                                             | **[FACT]**                   |
| Q4  | When retrieved notes **conflict**, explicitly surface the conflict                        | **[FACT]**                   |
| Q4a | State **both** sides                                                                      | **[FACT]**                   |
| Q4b | Either say which one it’s trusting and **why**, **or** ask the user which is current      | **[FACT]**                   |
| Q4c | Never silently merge or pick one and present it as uncontested fact                       | **[FACT]**                   |
| Q5  | When the KB doesn’t cover the question, the agent **may** use **live web search** instead | **[FACT]**                   |
| Q5a | Live-search answers must be **clearly labeled** as from live search                       | **[FACT]**                   |
| Q5b | Must **not** blend live search as if it came from the user’s own notes                    | **[FACT]**                   |
| Q5c | Alternative allowed by constraints: say plainly that it isn’t covered                     | **[FACT]** (see Constraints) |


---



## 4. Expected inputs and outputs



### 4.1 Inputs


| Input                     | Description                                                                      | Type       |
| ------------------------- | -------------------------------------------------------------------------------- | ---------- |
| Raw note                  | Short **text file**: quick thought, pasted article excerpt, or meeting takeaways | **[FACT]** |
| `dump/` folder            | **15–20** raw, unorganized sample notes to seed the KB before recording the demo | **[FACT]** |
| Conflict pair in `dump/`  | Includes **at least one pair** where a later note contradicts an earlier one     | **[FACT]** |
| Natural-language question | User question against the ingested knowledge base                                | **[FACT]** |
| New notes at review time  | Agent must work on **any new note** added at review time, not only `dump/`       | **[FACT]** |


**[FACT]** Use `dump/` as the ingestion test set; you do **not** need to write your own sample notes.

**[OPEN]** At analysis time, `dump/` was **not present** in this repository. Confirm when/how sample notes are provided.

**[ASSUMPTION]** Ingestion is invoked per note (or per file in `dump/`), consistent with “Given one new raw note.”

**[OPEN]** Interface for inputs is not specified (CLI, script, notebook, API, chat UI, etc.).

### 4.2 Outputs (behavioral)


| Scenario               | Expected output behavior                                                                                                                  | Type       |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Successful ingest      | Note stored persistently; agent-chosen tags/categories; links to related notes where relevant; conflict relationship recorded if detected | **[FACT]** |
| Answerable question    | Answer grounded only in retrieved notes + citations to note(s)                                                                            | **[FACT]** |
| Conflicting evidence   | Explicit conflict surfacing (both sides; trust+why **or** ask user)                                                                       | **[FACT]** |
| Uncovered question     | Clearly labeled live search **or** plain “not covered”                                                                                    | **[FACT]** |
| Tool/retrieval failure | Graceful handling — **no crashes**                                                                                                        | **[FACT]** |


**[OPEN]** Exact citation format (filename, ID, quote snippet, path) is not specified.

**[OPEN]** Whether ingestion returns a visible summary of tags/links/conflicts is not specified (demo likely needs some visibility).

---



## 5. Key workflows / use cases



### Workflow A — Seed / ingest **[FACT]**

1. Start with (or process) notes from `dump/` (or a visible subset for the demo).
2. For each raw note, run curator ingestion:
  - Persist into KB.
  - Content-based tagging/categorization.
  - Link to related existing notes where relevant.
  - Detect/record conflicts with existing notes.
3. Knowledge base survives process restarts.



### Workflow B — Answer with citation **[FACT]** (demo required)

1. User asks a natural-language question covered by the KB.
2. Agent retrieves relevant notes via embeddings-based semantic search (not whole-KB stuffing).
3. Agent answers from retrieved content only and cites specific note(s).



### Workflow C — Conflict at query time **[FACT]** (demo required)

1. User asks a question that touches the two conflicting notes.
2. Agent retrieves both (and/or uses recorded conflict relationship).
3. Agent **explicitly** surfaces the conflict (does not silently pick one).



### Workflow D — Out-of-coverage **[FACT]** (demo required)

1. User asks a question the KB does not cover.
2. Agent either:
  - Falls back to **clearly labeled** live web search, **or**
  - Says plainly it isn’t covered.
3. Must not present external material as if from the user’s notes.



### Workflow E — Review-time new note **[FACT]**

1. Reviewer adds a new raw note (not from `dump/`).
2. Agent ingests and organizes it under the same curator rules.
3. Subsequent Q&A can use it.



### Workflow F — Failure handling **[FACT]**

1. Embedding call fails and/or search fails.
2. Agent handles gracefully (error messaging / degraded path); process does not crash.

---



## 6. Constraints and assumptions



### Hard constraints **[FACT]**

1. Ingestion and organization decisions (tags/links) must be made **by the agent per note**, not by a fixed rule tied to file type or source.
2. Retrieval must use **real embeddings-based semantic search** — keyword search alone does **not** satisfy the requirement.
3. Conflicting notes must be surfaced **explicitly at query time**, never silently resolved without saying so.
4. A question outside KB coverage must be answered by **clearly labeled live search** **or** a plain “not covered” answer — never as if from the user’s notes when it wasn’t.
5. Tool/retrieval failures (embedding call fails, search fails) must be handled gracefully — **no crashes**.
6. Persistence must survive **separate program runs**.
7. Do not put the **entire** knowledge base into one prompt for answering.
8. Answers must use **only** what’s actually retrieved (for KB-backed answers).



### Soft / free choices **[FACT]**

- Any embeddings provider, vector store, and agent framework is fine if requirements are met.
- Not restricted to any specific Model Context Protocol (MCP) or standard pattern.
- Free to use any AI coding IDEs and development tools.
- Live web search is optional as a fallback strategy (alternative: admit not covered).



### Assumptions (not stated as facts)


| Assumption                                                                                                                                                     | Type                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| “Local” means runs on the developer/reviewer machine with local persistence (file-backed DB / local vector index), not a hosted multi-tenant service           | **[ASSUMPTION]**                   |
| A LLM (or similar model) will drive tagging, linking, conflict detection, and answer generation — problem says “agent” but does not mandate a particular model | **[ASSUMPTION]**                   |
| Sample notes in `dump/` are plain text files (problem says “short text file”)                                                                                  | **[ASSUMPTION]**                   |
| Demo can use a subset of `dump/` if full ingest is shown as representative                                                                                     | **[FACT]** (“or a visible subset”) |


---



## 7. Technical requirements or considerations



### Explicitly required / allowed **[FACT]**


| Topic               | Requirement                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| Persistence         | Local vector store / embedding index that survives process restarts                               |
| Retrieval           | Embeddings-based semantic search                                                                  |
| Stack freedom       | Any embeddings provider, vector store, agent framework                                            |
| MCP                 | Not required / not restricted to a specific MCP pattern                                           |
| Prototype scope     | Local working prototype suitable for screen-recorded demo                                         |
| Production thinking | Architecture note must explain current architecture **and** how it would look at production scale |




### Not specified (do not treat as requirements)


| Topic                                                                     | Status                                                                                |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Language / runtime                                                        | **[OPEN]** — repo currently has Python scaffolding; problem does not mandate language |
| UI vs CLI                                                                 | **[OPEN]**                                                                            |
| Embedding model / LLM vendor                                              | **[OPEN]** (any that satisfies requirements)                                          |
| Exact vector DB product                                                   | **[OPEN]** (“any local vector store”)                                                 |
| Chunking strategy for notes                                               | **[OPEN]**                                                                            |
| Whether links/conflicts live in the vector store metadata vs a side store | **[OPEN]**                                                                            |
| Auth, multi-user, sync, cloud deploy                                      | Not required for prototype **[ASSUMPTION]**                                           |




### Reliability **[FACT]**

- Graceful handling of embedding/search failures; no crashes.

---



## 8. Potential edge cases

Derived from stated requirements; useful for testing. Marked as **[ASSUMPTION]** where not explicit.


| Edge case                                       | Why it matters                                  | Type                          |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------- |
| New note contradicts an earlier note            | Must detect, record, surface at query           | **[FACT]**                    |
| Question retrieves conflicting pair             | Must state both; trust+why or ask user          | **[FACT]**                    |
| Question outside KB                             | Labeled live search or “not covered”            | **[FACT]**                    |
| Embedding API failure during ingest or query    | No crash                                        | **[FACT]**                    |
| Live / web search failure                       | No crash; graceful handling                     | **[FACT]**                    |
| Duplicate or near-duplicate note ingested       | Relatedness vs conflict unclear                 | **[OPEN]** / **[ASSUMPTION]** |
| Partial overlap (updates one fact, rest agrees) | Conflict scope may be partial                   | **[ASSUMPTION]**              |
| Empty / very short note                         | Tagging/linking quality                         | **[ASSUMPTION]**              |
| Note related to many existing notes             | How many links to create                        | **[OPEN]**                    |
| Retrieval returns nothing relevant              | Treat as uncovered                              | **[ASSUMPTION]**              |
| Retrieval returns weakly related notes          | Risk of hallucinated grounding vs “not covered” | **[ASSUMPTION]**              |
| Re-ingest same file twice                       | Idempotency not specified                       | **[OPEN]**                    |
| Restart process then query                      | Persistence must still work                     | **[FACT]**                    |
| Reviewer adds arbitrary new note at review      | Must work beyond `dump/`                        | **[FACT]**                    |
| Keyword-only would match but semantics differ   | Must still use embeddings retrieval             | **[FACT]**                    |


---



## 9. Open questions / ambiguities

1. `dump/` **location / delivery** — Referenced as provided, but not currently in this repo. **[OPEN]**
2. **Citation granularity** — Filename? Note ID? Quoted span? Timestamp? **[OPEN]**
3. **Conflict storage vs detection-at-query** — Must record relationship at ingest **and** surface at query; whether query also re-checks for conflicts among retrieved notes is implied but mechanics are free. **[ASSUMPTION]** / **[OPEN]**
4. **“Trusting and why” criteria** — Recency? Confidence? Source type? Not specified. **[OPEN]**
5. **Live search provider** — Any allowed; labeling requirement is the hard part. **[OPEN]** for choice
6. **Interface** — CLI, TUI, simple web UI, notebook — not specified. **[OPEN]**
7. **Tag/link schema** — Free-form tags? Hierarchical categories? Bidirectional links? **[OPEN]**
8. **Idempotent ingest / updates / deletes** — Not mentioned. **[OPEN]**
9. **Multi-note batch ingest UX** — Demo shows ingesting dump or subset; per-note agent decisions still required. **[FACT]** + **[OPEN]** on batch API shape
10. **Evaluation of “content-based” organization** — How strictly reviewers check against hardcoded taxonomies. **[ASSUMPTION]** they will inspect that tags/links vary with content
11. **Offline mode** — If no network, live search fallback unavailable; “not covered” path still satisfies constraints. **[ASSUMPTION]**

---



## 10. Expected deliverables

All of the following are **required** for a complete submission **[FACT]**.

### 10.1 Git repository

- Full source code in a **public GitHub repo**.
- **README** with:
  - Setup instructions
  - Environment variables
  - How to run both the **ingestion** and **query** steps locally



### 10.2 Screen recording (5–10 minutes)

Must cover **code walkthrough** and a **demo** of the flow. Recording **must show**:

1. Ingesting the provided `dump/` notes (or a visible subset) into the knowledge base.
2. Asking a question that correctly retrieves and **cites** a specific note.
3. Asking a question that touches the **two conflicting notes**, with the agent **explicitly surfacing** the conflict (not silently picking one).
4. Asking a question the KB doesn’t cover, and handling via **clearly labeled live search** or a plain **“not covered”** answer.



### 10.3 Submission note

- **3–5 sentences** on what you would improve or extend given more time, and any trade-offs made.



### 10.4 Architecture note

- Explanation of **current architecture**.
- How it would look at **production-level scale**.



### 10.5 Post-submission

- Review call: architecture walkthrough, key decisions, live demo **[FACT]**.

---



## 11. Demo acceptance checklist (from problem statement)

Use this as a gate before recording **[FACT]**:

- [ ] Persistence: ingest, restart program, still queryable
- [ ] Agent-driven tags/links (not file-type rules / hardcoded taxonomy)
- [ ] Embeddings-based semantic retrieval (not keyword-only; not whole-KB prompt dump)
- [ ] Answer cites source note(s)
- [ ] Conflict pair surfaced explicitly at query time
- [ ] Out-of-coverage path labeled live search **or** plain not covered
- [ ] Failures do not crash the program
- [ ] Works on arbitrary new notes (not only `dump/`)
- [ ] README / env / run instructions present
- [ ] Public GitHub repo
- [ ] 5–10 min recording covering required scenes
- [ ] Submission note (3–5 sentences)
- [ ] Architecture note (current + production scale)

---



## 12. Non-goals (for the prototype)

Stated or clearly out of scope for the required prototype:


| Non-goal                                       | Basis                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------ |
| Building a full production multi-tenant system | Prototype + separate architecture note for scale **[FACT]** / **[ASSUMPTION]** |
| Hand-authoring sample notes                    | `dump/` provided; writing your own not required **[FACT]**                     |
| Mandating MCP                                  | Explicitly unrestricted **[FACT]**                                             |
| Keyword-only search as primary retrieval       | Explicitly insufficient **[FACT]**                                             |
| Silently resolving conflicts                   | Explicitly forbidden **[FACT]**                                                |


---



## 13. Source traceability


| Topic                       | Source section in PDF         |
| --------------------------- | ----------------------------- |
| Title / format / submission | Header table                  |
| Problem narrative           | Problem Statement             |
| Curator + Q&A behaviors     | What to Build                 |
| `dump/` seed notes          | Provided                      |
| Hard rules                  | Constraints                   |
| Tooling freedom             | Tool Usage Guidelines         |
| Repo, recording, notes      | Deliverables                  |
| Required demo scenes        | Screen Recording Must Show    |
| Effort / deadline           | Submission deadline paragraph |
| Review call                 | What Happens After Submission |


---

*Last updated from analysis of* `problem_statement/Notes Ingestion & Recall Agent Task.pdf`*. Do not treat implementation choices in code as requirements unless they map back to **[FACT]** items above.*