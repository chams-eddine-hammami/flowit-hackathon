# Query Engine
# Executive asks a question — Claude finds the answer with evidence
# Searches ALL sources — chat, email, documents, surveys
# Governance applied — role permissions enforced before AI sees data

import anthropic
import json
import os
from dotenv import load_dotenv
from normalization.database import get_connection
from governance.access_control import filter_results_by_role, get_allowed_sources

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def ask_claude(question: str, context_docs: list) -> dict:
    context = ""
    evidence = []

    for i, doc in enumerate(context_docs[:8]):
        context += f"\n[SOURCE {i+1}]"
        context += f"\nType: {doc['source_type']}"
        context += f"\nFrom: {doc['author_email']}"
        context += f"\nDate: {doc['timestamp']}"
        context += f"\nContent: {doc['content'][:300]}"
        context += "\n---"

        evidence.append({
            "source": doc['source_system'],
            "author": doc['author_email'],
            "date": str(doc['timestamp']),
            "type": doc['source_type'],
            "preview": doc['content'][:150]
        })

    prompt = f"""You are an intelligent executive assistant for Alpenblick Hospitality.
Answer based ONLY on the documents provided.
Be direct and concise — this is for a busy executive on mobile.
If the documents contain relevant information — use it.
If not — say clearly what is missing.

QUESTION: {question}

DOCUMENTS:
{context}

Respond ONLY with valid JSON — no markdown:
{{
    "answer": "direct answer in 2-3 sentences maximum",
    "confidence": "high or medium or low",
    "key_finding": "the single most important thing the executive should know",
    "action_needed": "what action should be taken, or null if none",
    "uncertainty": "what you are not sure about, or null if confident"
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
        result["evidence"] = evidence
        return result

    except Exception as e:
        return {
            "answer": "Could not process this question.",
            "confidence": "low",
            "key_finding": "System error",
            "action_needed": None,
            "uncertainty": str(e),
            "evidence": []
        }


def query(question: str, role: str = "CEO — Full Access") -> dict:
    print(f"\n🔍 Searching for: {question}")
    print(f"🔐 Role: {role}")

    conn = get_connection()
    cursor = conn.cursor()

    keywords = question.lower().replace("?", "").split()
    conditions = []
    params = []

    for keyword in keywords:
        if len(keyword) > 3:
            conditions.append("LOWER(r.content) LIKE ?")
            params.append(f"%{keyword}%")

    if not conditions:
        return {
            "answer": "Question too short to search.",
            "confidence": "low",
            "key_finding": "No keywords found",
            "action_needed": None,
            "uncertainty": None,
            "evidence": []
        }

    where_clause = " OR ".join(conditions)

    # Step 1 — Search unstructured (chat, email, docs)
    cursor.execute(f"""
        SELECT
            r.id, r.source_system, r.source_type,
            r.author_email, r.timestamp, r.content,
            r.metadata, e.sentiment,
            e.people_mentioned, e.projects_mentioned,
            e.decisions
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type IN ('chat_messaging', 'email', 'document')
        AND ({where_clause})
        ORDER BY r.timestamp DESC
        LIMIT 5
    """, params)
    unstructured = cursor.fetchall()

    # Step 2 — Search survey data
    cursor.execute(f"""
        SELECT
            r.id, r.source_system, r.source_type,
            r.author_email, r.timestamp, r.content,
            r.metadata, e.sentiment,
            e.people_mentioned, e.projects_mentioned,
            e.decisions
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND ({where_clause})
        ORDER BY r.timestamp DESC
        LIMIT 5
    """, params)
    surveys = cursor.fetchall()

    conn.close()

    # Combine — unstructured first then surveys
    all_results = list(unstructured) + list(surveys)

    # ── GOVERNANCE — filter by role ──────────────────────────
    filtered_results = filter_results_by_role(all_results, role)

    # If results exist but ALL blocked by governance
    if not filtered_results and all_results:
        return {
            "answer": "🔒 Access denied. You do not have permission to view this information.",
            "confidence": "high",
            "key_finding": "This content is restricted for your role.",
            "action_needed": "Contact your administrator if you need access.",
            "uncertainty": None,
            "evidence": [],
            "access_denied": True
        }

    # If nothing found at all
    if not filtered_results:
        return {
            "answer": "No relevant information found in any source.",
            "confidence": "low",
            "key_finding": "No data found across any connected source",
            "action_needed": "Check if the relevant data source is connected",
            "uncertainty": "No matching documents in database",
            "evidence": []
        }

    print(f"📚 Found {len(list(unstructured))} operational docs + {len(list(surveys))} survey responses")
    print(f"✅ After governance filter: {len(filtered_results)} documents allowed for this role")

    result = ask_claude(question, filtered_results)
    return result


def run_test_queries():
    """10 executive questions covering all data sources."""

    questions = [
        "What is the status of the Lucerne Guest Experience Initiative?",
        "How is morale in Lucerne Operations team?",
        "What did the CFO decide about the Freiburg budget?",
        "Who owns the Lucerne Guest Experience Initiative?",
        "What is causing the delay in the Lucerne project?",
        "How satisfied are employees with their current role?",
        "What are the main reasons employees are leaving the company?",
        "How do employees rate their work life balance?",
        "What is the overall sentiment across all teams?",
        "What feedback did employees give about management?"
    ]

    print("\n🎯 EXECUTIVE QUERY TEST — 10 QUESTIONS")
    print("=" * 60)

    for i, question in enumerate(questions):
        print(f"\n❓ QUESTION {i+1}: {question}")
        result = query(question)
        print(f"✅ ANSWER     : {result['answer']}")
        print(f"📊 CONFIDENCE : {result['confidence']}")
        print(f"⚡ KEY FINDING: {result['key_finding']}")
        print(f"🎯 ACTION     : {result['action_needed']}")
        if result.get('uncertainty'):
            print(f"⚠️  UNCERTAINTY: {result['uncertainty']}")
        print(f"📎 EVIDENCE ({len(result['evidence'])} sources):")
        for e in result['evidence'][:2]:
            print(f"   - {e['type']} | {e['author']} | {str(e['date'])[:10]}")
        print("-" * 60)


if __name__ == "__main__":
    run_test_queries()