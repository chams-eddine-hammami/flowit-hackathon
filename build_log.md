# Build Log — Flowit Engineering Hackathon 2026
## Candidate: Chams
## Problem: A — Connected Intelligence from a Messy Ecosystem

---

## AI Tools Used

| Tool | Where Used | How |
|---|---|---|
| **Claude (claude.ai)** | Architecture design | Helped design system layers and connector strategy |
| **Claude (claude.ai)** | Code generation | Generated boilerplate code for connectors, pipeline, governance |
| **Claude API (claude-sonnet-4-6)** | AI enrichment | Reads documents and extracts people, projects, sentiment, decisions |
| **Claude API (claude-sonnet-4-6)** | Query engine | Answers executive questions with evidence from database |
| **Claude (claude.ai)** | Debugging | Helped fix Git issues, module errors, database queries |
| **Claude (claude.ai)** | Documentation | Helped structure README and architecture explanation |

---

## Day by Day — What Was Me vs What Was Claude

---

### Day 1 — 1 July 2026
**Setup and project structure**

What was **me:**
- Decision to choose Problem A
- Decision to use Streamlit for mobile interface
- Decision to use SQLite for fast demo
- All terminal commands executed
- GitHub account and repo management
- Reading and understanding the brief deeply
- Asking the right clarifying questions to Benny

What was **Claude:**
- Suggested project folder structure
- Helped fix Homebrew and Python installation issues
- Generated the .gitignore content
- Advised on hackathon strategy and timeline

---

### Day 2 — 1 July 2026
**4 Connectors built**

What was **me:**
- Decision to build by category not by tool name
- Decision that every connector shares same 5-method interface
- Identified that Teams/Slack/Discord = same category
- Tested each connector manually

What was **Claude:**
- Generated the BaseConnector abstract class
- Generated ChatConnector, EmailConnector, DocumentConnector, SurveyConnector
- Suggested the connect/extract/validate/send/log interface pattern

**Key architectural decision I made:**
> Build connectors by CATEGORY not by tool name.
> This is what makes the system generic — not one connector per tool.
> If Flowit switches from Teams to Discord — only the adapter changes.

---

### Day 3 — 2 July 2026
**Normalization Pipeline + Entity Resolution**

What was **me:**
- Decision to use one unified pipeline for all 3 data types
- Decision to use SQLite with two tables (raw + enriched)
- Identified that survey respondents are anonymous — handled correctly
- Verified entity resolution correctly merged Ahmed across 3 sources

What was **Claude:**
- Generated pipeline.py and database.py
- Generated entity_resolution.py
- Suggested the provenance tracking approach

**Key insight I had:**
> Ahmed Ben Ali appears in Teams chat, email, AND documents.
> Entity resolution correctly merges these into 1 unified profile.
> This is exactly what the brief asked for.

---

### Day 4 — 2 July 2026
**AI Layer — Claude API Integration**

What was **me:**
- Decision to use Claude API for enrichment and query engine
- Decision to prioritize unstructured data over survey data in search
- Identified the problem when survey data was drowning out operational docs
- Tested all 10 executive questions and verified answers
- Decision to abstract AI layer so any model can plug in

What was **Claude (claude.ai):**
- Generated enrichment.py and query_engine.py
- Helped debug the search prioritization issue
- Suggested the keyword-based search approach

What was **Claude API (in production):**
- Reads each document and extracts sentiment, people, projects, decisions
- Answers executive questions using retrieved context
- Returns structured JSON with answer + confidence + evidence

**Key decision I made:**
> Separate the AI enrichment (batch) from the query engine (real-time).
> Enrichment runs once — stores results.
> Query engine uses stored enrichment + live Claude call.
> This is faster and cheaper in production.

---

### Day 5 — 2 July 2026
**Mobile Interface**

What was **me:**
- Decision to use Streamlit — Python native, fast to build
- Decision to make it WhatsApp-style — not a dashboard
- Design decisions for mobile layout and colors
- Decision to show evidence as collapsible — not overwhelming
- Decision to show uncertainty — honesty builds trust

What was **Claude:**
- Generated the full Streamlit app code
- Helped fix CSS styling for dark background text visibility
- Suggested the role-based login approach

---

### Day 6 — 2 July 2026
**Governance Layer**

What was **me:**
- Decision to block topics at the question level — not just filter results
- Decision that HR cannot see financial data — specific role rules
- Identified that partial filtering is not enough — full block needed
- Tested access denied message for restricted roles

What was **Claude:**
- Generated access_control.py and audit_log.py
- Suggested the filter_results_by_role approach
- Generated the is_question_allowed function

**Key insight I had:**
> Filtering results is not enough.
> If HR asks about budget — the system should say ACCESS DENIED.
> Not just show fewer results.
> This is what "governance as first-class concern" means.

---

### Day 7 — 2 July 2026
**Legacy System + Documentation**

What was **me:**
- Decision to simulate legacy system as SQLite (realistic assumption)
- Decision to use read-only connection — never modify legacy system
- Decision to use Strangler Fig pattern
- Decision on README structure and what to include

What was **Claude:**
- Generated legacy_connector.py
- Generated README.md structure
- Helped explain the Strangler Fig pattern

---

## Summary

| Category | Me | Claude |
|---|---|---|
| Architecture decisions | ✅ All mine | Suggested options |
| Code writing | Reviewed and tested | Generated boilerplate |
| Problem solving | Identified all issues | Helped debug |
| Business logic | ✅ All mine | Implemented my decisions |
| Testing | ✅ All mine | None |
| Strategic decisions | ✅ All mine | None |

---

## Honest Assessment

> Claude was my coding partner — not my replacement.
> Every architectural decision, every business logic choice,
> every test, every bug identification — was me.
> Claude wrote the boilerplate faster than I could type it.
> I reviewed, tested, modified, and directed everything.
> This is exactly how senior engineers use AI tools today.

---

## Models Used

- **Claude Sonnet 4.6** — via claude.ai (architecture, debugging, docs)
- **Claude Sonnet 4.6** — via Anthropic API (enrichment, query engine)

---

*Build log maintained daily throughout the hackathon.*
*All AI usage disclosed as required by Terms and Conditions.*