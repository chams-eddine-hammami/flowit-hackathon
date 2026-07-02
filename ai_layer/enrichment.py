# AI Enrichment Layer
# Claude reads each document and extracts structured intelligence

import anthropic
import json
import os
from dotenv import load_dotenv
from normalization.database import get_connection

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def enrich_document(doc_id: int, content: str, source_type: str) -> dict:
    prompt = f"""You are an intelligent data analyst for a company.
Analyze this {source_type} and extract key information.

DOCUMENT:
{content}

Respond ONLY with a valid JSON object — no explanation, no markdown:
{{
    "people_mentioned": ["list of people or emails mentioned"],
    "projects_mentioned": ["list of projects mentioned"],
    "sentiment": "positive or negative or neutral or unclear",
    "key_topics": ["list of main topics"],
    "decisions": ["list of decisions or actions mentioned"],
    "summary": "one sentence summary of this document"
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result

    except Exception as e:
        print(f"  ⚠️ Error enriching document {doc_id}: {e}")
        return {
            "people_mentioned": [],
            "projects_mentioned": [],
            "sentiment": "unclear",
            "key_topics": [],
            "decisions": [],
            "summary": "Could not analyze"
        }


def store_enrichment(doc_id: int, enrichment: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM enriched_documents WHERE raw_document_id = ?",
        (doc_id,)
    )
    if cursor.fetchone():
        conn.close()
        return

    cursor.execute("""
        INSERT INTO enriched_documents
        (raw_document_id, people_mentioned, projects_mentioned,
         sentiment, key_topics, decisions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        doc_id,
        json.dumps(enrichment.get("people_mentioned", [])),
        json.dumps(enrichment.get("projects_mentioned", [])),
        enrichment.get("sentiment", "unclear"),
        json.dumps(enrichment.get("key_topics", [])),
        json.dumps(enrichment.get("decisions", []))
    ))

    conn.commit()
    conn.close()


def run_enrichment(limit: int = 20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, content, source_type
        FROM raw_documents
        WHERE source_type IN ('chat_messaging', 'email', 'document')
        AND id NOT IN (
            SELECT raw_document_id FROM enriched_documents
        )
        LIMIT ?
    """, (limit,))

    docs = cursor.fetchall()
    conn.close()

    if not docs:
        print("✅ All documents already enriched!")
        return

    print(f"\n🤖 Enriching {len(docs)} documents with Claude AI...")
    print("=" * 50)

    for doc in docs:
        print(f"\n📄 Analyzing document {doc['id']} ({doc['source_type']})...")
        enrichment = enrich_document(doc['id'], doc['content'], doc['source_type'])
        store_enrichment(doc['id'], enrichment)
        print(f"  ✅ Sentiment  : {enrichment['sentiment']}")
        print(f"  ✅ Projects   : {enrichment['projects_mentioned']}")
        print(f"  ✅ People     : {enrichment['people_mentioned']}")
        print(f"  ✅ Summary    : {enrichment['summary']}")

    print("\n" + "=" * 50)
    print(f"✅ Enrichment complete — {len(docs)} documents analyzed!")


if __name__ == "__main__":
    run_enrichment()