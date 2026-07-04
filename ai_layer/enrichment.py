# AI Enrichment Layer
# Claude reads each document and extracts structured intelligence
# Supports ALL languages — English, German, Arabic, French, Italian,
# Spanish, Portuguese, Japanese, Korean, Chinese and more

import anthropic
import json
import os
from dotenv import load_dotenv
from normalization.database import get_connection

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def enrich_document(doc_id: int, content: str, source_type: str) -> dict:
    """
    Send one document to Claude and extract structured intelligence.
    Handles ANY language automatically.
    """
    prompt = f"""You are an intelligent data analyst for a hospitality company.
Analyze this {source_type} and extract key information.

CRITICAL LANGUAGE RULES:
- The content may be in ANY language: English, German, Arabic, French,
  Italian, Spanish, Portuguese, Japanese, Korean, Chinese, or others.
- Always analyze the content regardless of language.
- Always respond in ENGLISH only.
- Detect the language and translate if not English.
- Example: German "sehr unzufrieden" = very unsatisfied = negative sentiment
- Example: Arabic "أعتقد أن تحسين توزيع المهام" = I think improving task distribution
- Example: Japanese "もう少し業務の裁量" = more discretion in work

DOCUMENT:
{content}

Respond ONLY with a valid JSON object — no explanation, no markdown:
{{
    "people_mentioned": ["list of people or emails mentioned"],
    "projects_mentioned": ["list of projects or initiatives mentioned"],
    "sentiment": "positive or negative or neutral or unclear",
    "key_topics": ["list of main topics in English"],
    "decisions": ["list of decisions or actions mentioned"],
    "summary": "one sentence summary in English",
    "detected_language": "the language of the original content in English",
    "translated_content": "English translation if not already in English, else null"
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
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
            "summary": "Could not analyze",
            "detected_language": "unknown",
            "translated_content": None
        }


def store_enrichment(doc_id: int, enrichment: dict):
    """Store Claude's analysis in the database."""
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
    """
    Enrich documents with AI analysis.
    Now includes survey text answers in any language.
    Skips numeric-only survey answers.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, content, source_type
        FROM raw_documents
        WHERE (
            source_type IN ('chat_messaging', 'email', 'document')
            OR (
                source_type = 'survey'
                AND LENGTH(content) > 100
                AND content NOT LIKE 'Q: How satisfied%'
                AND content NOT LIKE 'Q: I would recommend%'
                AND content NOT LIKE 'Q: I feel motivated%'
                AND content NOT LIKE 'Q: My workspace%'
                AND content NOT LIKE 'Q: The company provides%'
                AND content NOT LIKE 'Q: My direct manager%'
                AND content NOT LIKE 'Q: I trust the%'
                AND content NOT LIKE 'Q: I see opportunities%'
                AND content NOT LIKE 'Q: I am able%'
                AND content NOT LIKE 'Q: My team%'
                AND content NOT LIKE 'Q: I feel my%'
            )
        )
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
    print(f"   Includes multilingual survey answers")
    print("=" * 50)

    for doc in docs:
        print(f"\n📄 Analyzing document {doc['id']} ({doc['source_type']})...")
        enrichment = enrich_document(
            doc['id'], doc['content'], doc['source_type']
        )
        store_enrichment(doc['id'], enrichment)

        # Show language detected
        lang = enrichment.get('detected_language', 'English')
        print(f"  🌍 Language  : {lang}")
        print(f"  ✅ Sentiment : {enrichment['sentiment']}")
        print(f"  ✅ Topics    : {enrichment['key_topics']}")
        print(f"  ✅ Summary   : {enrichment['summary']}")
        if enrichment.get('translated_content'):
            print(f"  🔄 Translated: {enrichment['translated_content'][:80]}...")

    print("\n" + "=" * 50)
    print(f"✅ Enrichment complete — {len(docs)} documents analyzed!")


if __name__ == "__main__":
    run_enrichment()