# Build Log — Flowit Engineering Hackathon 2026

## Candidate: Chams Eddine Hammami
## Problem: A — Connected Intelligence from a Messy Ecosystem
## Submission date: July 9, 2026

---

## AI Tools Disclosure

### Tools Used

| Tool | Purpose | Where in Code |
|------|---------|---------------|
| Claude Sonnet 4.6 (claude.ai) | Architecture design, debugging, documentation | All sessions |
| Claude Sonnet 4.6 (Anthropic API) | Document enrichment — sentiment, topics, entities | ai_layer/enrichment.py |
| Claude Sonnet 4.6 (Anthropic API) | RAG query engine — answers executive questions | ai_layer/query_engine.py |
| Claude Sonnet 4.6 (Anthropic API) | Multilingual translation — 8 languages | ai_layer/query_engine.py |

---

## AI and ML Techniques Used

### 1. RAG — Retrieval Augmented Generation
- **What it is:** Retrieve relevant documents → augment Claude prompt → generate grounded answer
- **Where:** ai_layer/query_engine.py — query() and ask_claude() functions
- **Why:** Prevents hallucination — Claude only answers from retrieved evidence
- **Innovation:** Smart routing routes people questions to survey data first, operational questions to chat/email first

### 2. LLM — Large Language Model
- **What it is:** Claude Sonnet 4.6 as the AI backbone
- **Where:** enrichment.py (analysis) + query_engine.py (answering)
- **Why:** Best reasoning quality, long context window, multilingual understanding
- **Innovation:** Used for both enrichment AND query answering — one model, two purposes

### 3. NLP — Natural Language Processing
- **What it is:** Extract structured intelligence from unstructured text
- **Where:** ai_layer/enrichment.py
- **Extracted:** sentiment, topics, people mentioned, projects, decisions, language detection
- **Languages:** German, Arabic, French, Italian, Portuguese, Korean, Japanese, English

### 4. Entity Resolution
- **What it is:** Match same person across 9 different data sources
- **Where:** common_model/entity_resolution.py
- **Result:** respondent_668738 appears in 9 sources → 1 unified profile
- **Method:** SQL aggregation by author_email across all raw_documents

### 5. Statistical Aggregation
- **What it is:** Calculate real survey averages from database
- **Where:** ai_layer/query_engine.py — get_all_averages(), get_team_satisfaction(), get_workload_by_team()
- **Result:** 10 score dimensions calculated from 22 employees × 3 survey periods = 66 data points per question
- **Innovation:** Pre-calculated at query time — never hardcoded

### 6. Keyword Expansion + Targeted Retrieval
- **What it is:** Expand query with synonyms + route by question type
- **Where:** ai_layer/query_engine.py — expand_keywords(), search_for_question_type()
- **Why:** Keyword search misses semantic matches — expansion bridges the gap
- **Innovation:** 6 targeted search patterns for exit, budget, engineering, morale, complaints, Lucerne questions

### 7. RBAC — Role-Based Access Control
- **What it is:** Permissions propagate from data source to AI surface
- **Where:** governance/access_control.py
- **Roles:** CEO (full), CFO (finance), HR (people), Operations (projects)
- **Innovation:** Permission check at question level — not just result filtering

### 8. ETL Pipeline — Extract Transform Load
- **What it is:** Ingest 9 data sources into one normalized schema
- **Where:** normalization/pipeline.py + all connectors
- **Records:** 1818 total records with full provenance tracking

---

## Agent Architecture

| Agent | File | Role |
|-------|------|------|
| Connector Agents (×9) | connectors/ | Ingest from each data source |
| Enrichment Agent | ai_layer/enrichment.py | Analyze documents with Claude |
| Query Agent (RAG) | ai_layer/query_engine.py | Answer questions with evidence |
| Governance Agent | governance/access_control.py | Enforce permissions before AI sees data |
| Entity Resolution Agent | common_model/entity_resolution.py | Link identities across 9 sources |

---

## Day by Day Build Log

### Day 1 — June 30, 2026 — Setup

**What was me:**
- Decision to choose Problem A
- Decision to use Streamlit for mobile interface
- Decision to use SQLite for demo — PostgreSQL in production
- Read brief deeply — identified 4 requirements
- GitHub repo setup and management

**What was Claude:**
- Suggested project folder structure
- Helped fix Python installation issues
- Generated .gitignore

---

### Day 2 — July 1, 2026 — Connector Layer

**What was me:**
- Decision to build by CATEGORY not by tool name
- Decision that every connector shares same 5-method interface
- Identified Teams/Slack/Discord = same category, different adapter
- Tested each connector manually

**What was Claude:**
- Generated BaseConnector abstract class
- Generated 9 connector implementations
- Suggested connect/extract/validate/send/log interface

**Key architectural decision I made:**
> Build connectors by CATEGORY not by tool name.
> If Flowit switches from Teams to Discord — only the adapter changes.
> The rest of the system is untouched.

---

### Day 3 — July 2, 2026 — Normalization + Common Model

**What was me:**
- Decision to normalize everything to one common schema
- Decision to track provenance on every single record
- Decision to build entity resolution using SQL aggregation
- Identified same respondent_id appears across 9 sources

**What was Claude:**
- Generated normalization/pipeline.py
- Generated common_model/entity_resolution.py
- Helped design database schema

**Key insight I had:**
> Without entity resolution — same person in 9 sources = 9 different people.
> With entity resolution — 1 unified profile with full context.

---

### Day 4 — July 3, 2026 — AI Enrichment Layer

**What was me:**
- Decision to enrich documents once and store results permanently
- Decision on what to extract: sentiment, topics, people, projects, decisions
- Decision to skip enrichment on numeric scores — calculate directly
- Total enrichment cost: ~$7 for 734 documents

**What was Claude:**
- Generated ai_layer/enrichment.py
- Suggested the store-once-reuse pattern
- Generated JSON extraction prompt

**Key decision:**
> Enrich once → store in DB → reuse forever.
> Fast and cost-efficient in production.

---

### Day 5 — July 4-5, 2026 — RAG Query Engine

**What was me:**
- Decision to use RAG architecture
- Decision on smart routing — people questions → survey first
- Decision on targeted search by question type
- Identified all retrieval failure modes and fixed them
- Tested all 20 demo questions manually

**What was Claude:**
- Generated query_engine.py structure
- Generated pre-calculated functions (get_all_averages etc.)
- Helped debug keyword expansion issues

**Key insight I had:**
> Retrieval quality > model quality.
> The best LLM gives wrong answers with wrong documents.
> Targeted retrieval by question type improved precision dramatically.

---

### Day 6 — July 6, 2026 — Governance Layer

**What was me:**
- Decision to block at question level — not just filter results
- Specific role rules: HR cannot see financial data
- Identified partial filtering is not enough — full block needed
- Tested access denied for all restricted role/topic combinations

**What was Claude:**
- Generated access_control.py and audit_log.py
- Generated is_question_allowed() function

**Key insight I had:**
> Filtering results after retrieval is not good enough.
> If HR asks about budget — system must say ACCESS DENIED before retrieval.
> Governance must propagate from source to surface.

---

### Day 7 — July 7-8, 2026 — Interface + Integration

**What was me:**
- All interface design decisions
- Mobile-first layout
- Evidence card format
- Role-based suggestion questions per persona
- All 20 demo questions tested and verified

**What was Claude:**
- Generated interface/app.py structure
- Helped fix evidence display bugs
- Generated role-based suggestion lists

---

### Day 8 — July 9, 2026 — Final Testing + Submission

**What was me:**
- Full demo readiness test 
- Architecture diagram designs
- All submission materials preparation
- Final GitHub push

**What was Claude:**
- Helped update build log and README

---

## Honest Assessment

> Claude was my senior coding partner — not my replacement.
>
> Every architectural decision, every business logic choice,
> every test, every bug identification — was me.
>
> Claude wrote boilerplate faster than I could type it.
> I reviewed, tested, modified, and directed everything.
>
> The hardest problems — retrieval quality, evidence grounding,
> smart routing, governance propagation — I solved by thinking not by asking Claude to think for me.
>
> This is exactly how senior engineers use AI tools today.

---

## Final Numbers

| Metric | Value |
|--------|-------|
| Total records ingested | 1818 |
| Documents enriched | 734 (40.4%) |
| Survey respondents | 38 unique employees |
| Survey text answers | 425 |
| Score responses | 1084 |
| Languages supported | 8 |
| Connectors built | 9 |
| Agent types | 5 |
| Governance roles | 4 |
| Days to build | 8 |
| Total API cost | ~$9 |

---

## Models Used

- **Claude Sonnet 4.6** via claude.ai — architecture, debugging, documentation
- **Claude Sonnet 4.6** via Anthropic API — enrichment, RAG query engine, translation

---

*Build log maintained throughout the hackathon.*
*All AI usage disclosed as required by the Flowit Hackathon Terms and Conditions.*
