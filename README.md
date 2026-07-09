# flowit AI — Connected Intelligence

**Flowit Engineering Hackathon 2026 — Problem A**  
**Candidate:** Chams Eddine Hammami

---

## What This System Does

One AI assistant that connects 9 enterprise data sources and answers executive questions with evidence.

---

## Architecture

See: docs/architecture.png
![alt text](docs/architecture.png)
---

## Requirements

Before starting make sure you have these installed:

- Python 3.10 or higher — check with: python3 --version
- pip latest — check with: pip --version
- Git any version — check with: git --version
- Anthropic API key — get from: https://console.anthropic.com/settings/keys

---

## Setup — Step by Step

---

### Step 1 — Clone the repository

Run this in your terminal:

    git clone https://github.com/chamseddinehammami18-debug/flowit-hackathon.git
    cd flowit-hackathon

Verify you are in the project folder:

    ls

You should see: connectors/ data/ ai_layer/ interface/ README.md

---

### Step 2 — Create Python virtual environment

On Mac or Linux:

    python3 -m venv hackathon-env
    source hackathon-env/bin/activate

On Windows:

    python3 -m venv hackathon-env
    hackathon-env\Scriptsctivate

Verify — you should see (hackathon-env) at the start of your terminal:

    (hackathon-env) your-computer flowit-hackathon %

If you do not see this — run the activate command again.

---

### Step 3 — Install all dependencies

    pip install streamlit anthropic python-dotenv pandas sqlalchemy

Wait 1-3 minutes until you see: Successfully installed ...

Verify all packages installed correctly:

    python3 -c "import streamlit, anthropic, pandas, sqlalchemy; print(All packages OK)"

Expected output:

    All packages OK

---

### Step 4 — Add your Anthropic API key

Get your key here: https://console.anthropic.com/settings/keys

Create the .env file:

    echo "ANTHROPIC_API_KEY=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" > .env

Verify the key is saved:

    cat .env

Expected output:

    ANTHROPIC_API_KEY=sk-ant-...

---

### Step 5 — Run the data pipeline

Run these 3 commands one by one. Wait for each to finish before running the next.

Command 1 — ingest all 9 data sources:

    python3 -m normalization.pipeline

Expected output:

    Survey responses : 1779
    TOTAL stored     : 1811

Command 2 — link same person across sources:

    python3 -m common_model.entity_resolution

Expected output:

    Entity resolution complete

Command 3 — add employee profiles:

    python3 -m connectors.legacy_connector

Verify the database was created:

    ls data/

You should see: flowit.db

---

### Step 6 — Start the application

    streamlit run interface/app.py

The app opens automatically at: http://localhost:8501

You should see the flowit AI login page.

---

## How to Use the App

Login with any name and select your role: CEO, CFO, HR Manager, or Operations Manager.

---

## Demo Questions

CEO:
- Why are employees leaving the company?
- Which project has the highest risk right now?
- What is the overall company morale?
- Summarize the Lucerne Guest Experience Initiative
- What are the biggest people risks at Alpenblick?

CFO:
- What is the Freiburg expansion budget status?
- Which projects have financial risks?
- What did the CFO decide about the Freiburg renovation?
- What are the open Jira tickets and their priorities?
- What is the status of the Lucerne initiative?

HR Manager:
- What are the main employee complaints?
- What are the main reasons for resignation?
- What do employees think about career development?
- Which teams have the lowest satisfaction scores?
- Which teams have low engagement?

Operations Manager:
- What operational issues exist right now?
- What are the current engineering blockers?
- Which Jira issues are delayed or blocked?
- What happened in the latest operations meeting?
- What is the status of the Lucerne initiative?

---

## Test Governance

Login as Operations Manager and ask: What is the Freiburg budget?

Expected: ACCESS DENIED — this topic is restricted for your role.

---

## Troubleshooting

Problem: ModuleNotFoundError

    source hackathon-env/bin/activate
    pip install streamlit anthropic python-dotenv pandas sqlalchemy

Problem: API key not found

    cat .env

Problem: Database errors

    python3 -m normalization.pipeline
    python3 -m common_model.entity_resolution
    python3 -m connectors.legacy_connector

Problem: Port already in use

    streamlit run interface/app.py --server.port 8502
    Then open: http://localhost:8502

Problem: App opens but no answers

    python3 -m ai_layer.query_engine


---

## Data Sources

- Survey CSV (Benny dataset) — Structured — 1779 records — Real data from Flowit
- Legacy HR SQL — Structured — 7 records
- Jira tickets — Structured — 4 records
- Teams chat — Semi-structured — 7 records
- Outlook email — Semi-structured — 5 records
- Slack messages — Semi-structured — 5 records
- Word documents — Unstructured — 5 records
- SharePoint files — Unstructured — 3 records
- Meeting notes — Unstructured — 3 records

Survey data is real data provided by Flowit (38 respondents, 8 languages).
All other sources simulate real APIs using real respondent IDs.
In production — each connector connects to the real API instead.

---

## AI and ML Techniques

- RAG (Retrieval Augmented Generation) — evidence-based answering, no hallucination
- LLM Claude Sonnet 4.6 — document enrichment and query answering
- NLP Entity extraction — people, projects, decisions from text
- NLP Sentiment analysis — positive/negative/neutral per document
- NLP Language detection — 8 languages auto-detected
- NLP Translation — non-English answers translated to English
- Entity resolution — same person across 9 sources equals 1 unified profile
- Statistical aggregation — real survey averages calculated from database
- Smart routing — people questions go to survey first, operational to chat/email first
- Targeted retrieval — question-type specific SQL queries for higher precision
- RBAC — role-based access control governance layer

---

## Project Structure

    flowit-hackathon/
    connectors/          9 data source connectors
    normalization/       ETL pipeline
    common_model/        Entity resolution
    ai_layer/            RAG query engine and enrichment
    governance/          RBAC access control
    interface/           Streamlit mobile app
    data/structured/     Survey CSV Benny dataset
    data/raw/            Simulated JSON data sources
    docs/                Architecture diagram
    build_log.md         Full AI usage disclosure
    README.md            This file

---

## What Would Come Next

- Vector search Pinecone/Weaviate for semantic retrieval
- Real-time streaming Kafka for live sentiment alerts
- More connectors Salesforce SAP Google Drive
- Fine-tuned model on company vocabulary
- Push notifications when sentiment drops

---

## Build Log

See build_log.md for full AI usage disclosure.

---

Built by Chams Eddine Hammami — Flowit Engineering Hackathon 2026
