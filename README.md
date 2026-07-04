# Flowit Intelligence Platform
## Hackathon Submission — Problem A
### Connected Intelligence from a Messy Ecosystem

---

## What This Is

A production-ready AI platform that connects scattered company data
from multiple sources, understands it, and surfaces the right answer
to the right person at the right moment — on mobile, with evidence.

Built for Alpenblick Hospitality as a demonstration.
Designed to work for any company.

---

## The Problem

Company data is scattered everywhere:
- Chat messages in Teams
- Emails in Outlook
- Documents in SharePoint
- Survey results in survey platforms
- Employee records in legacy HR systems

No one can see the full picture.
Executives waste time digging through tools.
Decisions are made without evidence.

---

## The Solution

One unified AI platform that:
1. **Ingests** data from any source — no hand-rolled integration per source
2. **Understands** it — entity resolution, relationships, provenance
3. **Surfaces** the right answer on mobile — with evidence
4. **Enforces** governance — permissions follow the data always

---

## Architecture

DATA SOURCES
Teams · Email · Documents · Surveys · Legacy HR System
↓
CONNECTOR LAYER (plug-in architecture)
One standard interface — 5 methods — add any source
↓
NORMALIZATION LAYER
Structured → mapped directly
Semi-structured → parsed
Unstructured → Claude AI extracts meaning
↓
COMMON MODEL (SQLite)
Entity resolution · Relationships · Provenance
↓
AI LAYER (Claude API)
Enrichment · Query engine · Evidence linking
↓
GOVERNANCE LAYER
Role-based access · Permissions filter before AI sees data
Audit log · Every access tracked
↓
MOBILE INTERFACE (Streamlit)
WhatsApp-style chat · Answer + evidence · Zero training needed

---

## The 4 Requirements

### 1. Ingest Heterogeneous Sources
- Chat connector (Teams / Slack / Discord)
- Email connector (Outlook / Gmail)
- Document connector (Word / Google Docs)
- Survey connector (Typeform / real Flowit dataset)
- Legacy SQL connector (read-only, never modifies old system)
- Generic connector (any REST API or CSV)

**Key principle:** New source = new connector only.
Nothing else changes.

### 2. Common Model
- Entity resolution: same person across sources → 1 unified profile
- Relationships: who works on what, who emailed who
- Provenance: every fact knows its source, author, and timestamp

### 3. Mobile-First Surface
- WhatsApp-style chat interface
- Works in any phone browser — no app install needed
- Answer in 2-3 sentences + key finding + action needed + evidence
- Zero training required

### 4. Governance as First-Class Concern
- Role-based access: CEO sees all, HR sees people data only
- Permissions enforced BEFORE data reaches Claude
- Blocked topics return "Access denied" — not partial data
- Every query logged with who, what, when

---

## Legacy System

The platform sits alongside an existing legacy SQL system
(Oracle/MySQL equivalent) without modifying it.

**Strategy:** Read-only connector bridges old and new.
Legacy system keeps running. New AI stack grows next to it.
This is the Strangler Fig pattern.

---

## Generality — The Real Test

> "A new source is a connector. A new use case is a config change."

Adding Microsoft Teams → implement 5 standard methods → done.
Switching to Slack → swap the adapter → nothing else changes.
New use case → update query questions → no rewrite needed.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Connectors | Python + standard interface | Plug-in architecture |
| Database | SQLite | Fast, portable, demo-ready |
| AI | Claude API (claude-sonnet-4-6) | Best reasoning + evidence |
| Interface | Streamlit | Python-native, mobile-friendly |
| Governance | Role-based access control | Built-in, not bolted-on |

---

## How to Run

```bash
# 1. Clone the repo
git clone https://github.com/chamseddinehammami18-debug/flowit-hackathon.git
cd flowit-hackathon

# 2. Create environment
python3 -m venv hackathon-env
source hackathon-env/bin/activate

# 3. Install dependencies
pip install streamlit anthropic python-dotenv sqlalchemy pandas

# 4. Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 5. Run the pipeline
python3 -m normalization.pipeline
python3 -m common_model.entity_resolution
python3 -m ai_layer.enrichment
python3 -m connectors.legacy_connector

# 6. Start the app
streamlit run interface/app.py
```

---

## Demo Questions to Try

- "What is the status of the Lucerne Guest Experience Initiative?"
- "How is morale in Lucerne Operations team?"
- "What did the CFO decide about the Freiburg budget?"
- "Why are employees leaving the company?"
- "What is the overall team sentiment?"
- "Who owns the Lucerne initiative?"

---

## What I Would Build Next

- Vector search (semantic similarity — not just keywords)
- Real-time streaming (Kafka for live sentiment alerts)
- More connectors (Jira, Salesforce, SAP)
- Fine-tuned model on company vocabulary
- Push notifications when sentiment drops


## What I Would Build Next

- **Vector search** (Pinecone / Weaviate) — replace keyword search with
  semantic similarity for better document retrieval. Currently we send
  the 15 most keyword-relevant documents to Claude. Vector search would
  send the 15 most semantically similar — significantly improving answer
  quality especially for multilingual content.

- **Real-time streaming** (Apache Kafka) — replace batch pipeline with
  live data ingestion for instant sentiment alerts.

- **More connectors** — Jira, Salesforce, SAP, SharePoint API.

- **Feedback loop** — executive rates answers → system learns what
  is useful → improves over time.

- **Fine-tuned model** — train on company-specific vocabulary for
  better entity recognition.
  

---

## Build Log

See `build_log.md` for full AI tool usage disclosure.

---

*Built by Chams — Flowit Engineering Hackathon 2026*
