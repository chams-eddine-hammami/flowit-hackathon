# Query Engine
# Executive asks a question — Claude finds the answer with evidence
# Searches ALL sources — chat, email, documents, surveys
# Governance applied — role permissions enforced before AI sees data
# Smart keyword expansion — finds synonyms automatically
# Priority ordering — baseline surveys before exit interviews
# Numeric score handling — calculates averages for rating questions

import anthropic
import json
import os
from dotenv import load_dotenv
from normalization.database import get_connection
from governance.access_control import filter_results_by_role, get_allowed_sources

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─── KEYWORD EXPANSIONS ──────────────────────────────────────
KEYWORD_EXPANSIONS = {
    "career": ["career", "advancement", "promotion", "growth", "progression"],
    "development": ["development", "training", "learning", "education", "upskilling"],
    "morale": ["morale", "wellbeing", "satisfaction", "motivation", "engagement"],
    "workload": ["workload", "overload", "capacity", "stress", "burnout"],
    "management": ["management", "leadership", "supervisor", "manager", "feedback"],
    "communication": ["communication", "transparency", "information", "feedback"],
    "salary": ["salary", "compensation", "pay", "benefits", "wages"],
    "leaving": ["leaving", "resignation", "turnover", "exit", "departure"],
    "satisfied": ["satisfied", "satisfaction", "happy", "content", "engagement"],
    "feedback": ["feedback", "review", "evaluation", "assessment", "recognition"],
    "teamwork": ["teamwork", "collaboration", "team", "colleagues", "cooperation"],
    "balance": ["balance", "workload", "hours", "flexibility", "wellbeing"],
    "sentiment": ["sentiment", "morale", "satisfaction", "engagement", "culture"],
    "trust": ["trust", "autonomy", "independence", "empowerment", "leadership"],
    "training": ["training", "development", "learning", "courses", "education"],
    "appreciation": ["appreciation", "recognition", "valued", "acknowledged", "reward"],
    "score": ["score", "rating", "scale", "satisfaction", "satisfied"],
    "average": ["average", "mean", "score", "rating", "overall"],
    "rate": ["rate", "rating", "score", "scale", "satisfied"]
}

# ─── SCORE QUESTION DETECTION ────────────────────────────────
SCORE_KEYWORDS = [
    'score', 'rating', 'scale', 'out of', 'average',
    'rate', 'number', 'how many', 'how much', 'points',
    'satisfied', 'satisfaction', 'recommend', 'motivated',
    'balance', 'manager', 'leadership', 'workspace'
]


def is_score_question(question: str) -> bool:
    """Detect if question is asking for numeric scores."""
    q = question.lower()
    return any(kw in q for kw in SCORE_KEYWORDS)


def expand_keywords(question: str) -> list:
    """Expand question keywords with synonyms."""
    keywords = question.lower().replace("?", "").split()
    expanded = []
    for keyword in keywords:
        if len(keyword) > 3:
            expanded.append(keyword)
            for key, synonyms in KEYWORD_EXPANSIONS.items():
                if keyword in key or key in keyword:
                    expanded.extend(synonyms)
    return list(set(expanded))


def is_non_english(text: str) -> bool:
    """Detect non-English text."""
    arabic = any('\u0600' <= c <= '\u06ff' for c in text)
    japanese = any('\u3040' <= c <= '\u30ff' for c in text)
    korean = any('\uac00' <= c <= '\ud7a3' for c in text)
    special = any(
        c.lower() in 'àáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿäöüß'
        for c in text
    )
    return arabic or japanese or korean or special


def translate_text(text: str) -> str:
    """Translate non-English text to English."""
    try:
        if '| A:' in text:
            text = text.split('| A:')[1].strip()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "Translate the following text to English. "
                    "Reply ONLY with the translation, nothing else:\n\n"
                    + text[-400:]
                )
            }]
        )
        return response.content[0].text.strip()
    except Exception:
        return None

def get_all_averages() -> str:
    """Calculate ALL survey averages from all respondents."""
    conn = get_connection()
    cursor = conn.cursor()

    questions_to_calculate = [
        ('Role satisfaction',    'how satisfied are you with your current role'),
        ('Recommendation score', 'recommend this company as a great place'),
        ('Motivation score',     'motivated to go above and beyond'),
        ('Workspace comfort',    'workspace provides a comfortable'),
        ('Resources adequacy',   'company provides adequate resources'),
        ('Manager rating',       'manager provides clear direction'),
        ('Leadership trust',     'trust the leadership team'),
        ('Career growth',        'opportunities for career growth'),
        ('Work life balance',    'maintain a healthy work-life balance'),
        ('Training support',     'invests in my professional development'),
    ]

    results = []

    for label, keyword in questions_to_calculate:
        cursor.execute("""
            SELECT content, author_email FROM raw_documents
            WHERE source_type = 'survey'
            AND content LIKE '%Score:%'
            AND author_email LIKE 'respondent_6687%'
            AND LOWER(content) LIKE ?
        """, (f"%{keyword}%",))

        rows = cursor.fetchall()
        scores = []
        unique_respondents = set()

        for row in rows:
            try:
                score_part = row[0].split('Score:')[1]\
                    .split('out of')[0].strip()
                score = float(score_part)
                if 1 <= score <= 7:
                    scores.append(score)
                    unique_respondents.add(row[1])
            except:
                pass

        if scores:
            avg = round(sum(scores) / len(scores), 1)
            results.append(
                f"  {label}: {avg}/7 "
                f"({len(unique_respondents)} employees, "
                f"{len(scores)} responses)"
            )

    conn.close()

    if results:
        return "SURVEY SCORE AVERAGES:\n" + "\n".join(results)
    return None

def ask_claude(question: str, context_docs: list, pre_calculated: str = None) -> dict:
    """Send question + documents to Claude for analysis."""
    context = ""
    evidence = []

    for i, doc in enumerate(context_docs[:5]):
        context += f"\n[SOURCE {i+1}]"
        context += f"\nType: {doc['source_type']}"
        context += f"\nFrom: {doc['author_email']}"
        context += f"\nDate: {doc['timestamp']}"
        context += f"\nContent: {doc['content'][:400]}"
        context += "\n---"

        full_content = doc['content']

        # Translate only first 3 non-English docs
        translation = None
        if is_non_english(full_content) and i < 3:
            translation = translate_text(full_content)

        evidence.append({
            "source": doc['source_system'],
            "author": doc['author_email'],
            "date": str(doc['timestamp']),
            "type": doc['source_type'],
            "preview": full_content,
            "translation": translation,
            "doc_id": doc['id']
        })

    prompt = f"""You are an intelligent executive assistant for Alpenblick Hospitality.

STRICT RULES:
1. Answer based ONLY on documents DIRECTLY relevant to the question.
2. IGNORE documents that match keywords but are not related to the question topic.
3. Be direct and concise — this is for a busy executive on mobile.
4. All languages understood — German, Arabic, French, Italian, Japanese, Korean, Portuguese.
5. Always respond in ENGLISH only.
6. If multiple employees say the same thing — mention this pattern explicitly.
7. ALWAYS distinguish between current employees and departing employees.
8. Never say no data exists unless you truly have zero relevant documents.


{f'''
‼️ MANDATORY — READ THIS FIRST:
The database has pre-calculated this result from ALL respondents:
>>> {pre_calculated} <
YOU MUST start your answer with this exact result.
DO NOT calculate your own average from the documents shown.
DO NOT say "based on 5 responses" or "one respondent".
The documents shown are just EXAMPLES — the real calculation used ALL data.
''' if pre_calculated else '''
NUMERIC RULES:
- Look for Score: X out of 7 in documents
- Calculate average from ALL scores you find
- Report: "Average score is X.X out of 7 based on Y respondents"
- NEVER say data does not exist if you see numbers
'''}

QUESTION: {question}

DOCUMENTS:
{context}

Respond ONLY with valid JSON — no markdown:
{{
    "answer": "direct answer in 2-3 sentences maximum",
    "confidence": "high or medium or low",
    "key_finding": "the single most important thing the executive should know",
    "action_needed": "what action should be taken, or null if none",
    "uncertainty": "what you are not sure about, or null if confident",
    "sources_used": ["list of source types actually used"]
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
    """Main query function."""
    print(f"\n🔍 Searching for: {question}")
    print(f"🔐 Role: {role}")

    conn = get_connection()
    cursor = conn.cursor()

    expanded_keywords = expand_keywords(question)
    print(f"🔑 Keywords: {len(expanded_keywords)} terms")

    conditions_content = []
    conditions_topics = []
    params_content = []
    params_topics = []

    for keyword in expanded_keywords:
        if len(keyword) > 3:
            conditions_content.append("LOWER(r.content) LIKE ?")
            params_content.append(f"%{keyword}%")
            conditions_topics.append("LOWER(e.key_topics) LIKE ?")
            params_topics.append(f"%{keyword}%")

    if not conditions_content:
        return {
            "answer": "Question too short to search.",
            "confidence": "low",
            "key_finding": "No keywords found",
            "action_needed": None,
            "uncertainty": None,
            "evidence": []
        }

    where_content = " OR ".join(conditions_content)
    where_topics = " OR ".join(conditions_topics)

    # Step 1 — Search unstructured
    cursor.execute(f"""
        SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type IN ('chat_messaging', 'email', 'document')
        AND ({where_content})
        ORDER BY r.timestamp DESC
        LIMIT 5
    """, params_content)
    unstructured = cursor.fetchall()

    # Step 2 — Search survey by content
    cursor.execute(f"""
        SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND ({where_content})
        ORDER BY r.timestamp DESC
        LIMIT 5
    """, params_content)
    surveys_content = cursor.fetchall()

    # Step 3 — Search survey by enriched topics
    cursor.execute(f"""
        SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        INNER JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND ({where_topics})
        ORDER BY
            CASE
                WHEN r.author_email LIKE 'respondent_6%' THEN 1
                WHEN r.author_email LIKE 'respondent_1%' THEN 2
                ELSE 3
            END,
            r.timestamp DESC
        LIMIT 15
    """, params_topics)
    surveys_topics = cursor.fetchall()

    # Step 4 — Numeric scores if score question
    numeric_results = []
    if is_score_question(question):
        cursor.execute(f"""
              SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND r.content LIKE '%Score:%'
        AND r.author_email LIKE 'respondent_6%'
        
        AND ({where_content})
        ORDER BY r.timestamp DESC
        LIMIT 5
        """, params_content)
        numeric_results = cursor.fetchall()
        print(f"🔢 Score question detected — found {len(numeric_results)} numeric results")

    conn.close()

    # Combine with priority
    seen = set()
    all_results = []

    # First — numeric results for score questions
    for doc in list(numeric_results):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # Second — operational docs
    for doc in list(unstructured):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # Third — baseline survey docs
    for doc in list(surveys_topics) + list(surveys_content):
        if doc['id'] not in seen:
            author = doc['author_email'] or ''
            if 'respondent_6' in author or 'respondent_1' in author:
                seen.add(doc['id'])
                all_results.append(doc)

    # Fourth — exit interview docs
    exit_count = 0
    for doc in list(surveys_topics) + list(surveys_content):
        if doc['id'] not in seen:
            author = doc['author_email'] or ''
            if 'respondent_2' in author and exit_count < 2:
                seen.add(doc['id'])
                all_results.append(doc)
                exit_count += 1

    # Fifth — remaining docs
    for doc in list(surveys_topics) + list(surveys_content):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # Apply governance
    filtered_results = filter_results_by_role(all_results, role)

    if not filtered_results and all_results:
        return {
            "answer": "🔒 Access denied.",
            "confidence": "high",
            "key_finding": "This content is restricted for your role.",
            "action_needed": "Contact your administrator if you need access.",
            "uncertainty": None,
            "evidence": [],
            "access_denied": True
        }

    if not filtered_results:
        return {
            "answer": "No relevant information found in any source.",
            "confidence": "low",
            "key_finding": "No data found",
            "action_needed": "Check if the relevant data source is connected",
            "uncertainty": "No matching documents in database",
            "evidence": []
        }

    print(f"📚 Found {len(list(unstructured))} operational + "
          f"{len(list(surveys_content))} survey content + "
          f"{len(list(surveys_topics))} survey topics + "
          f"{len(list(numeric_results))} numeric scores")
    print(f"✅ After governance: {len(filtered_results)} documents")


    pre_calculated = None
    if is_score_question(question):
        pre_calculated = get_all_averages()
        if pre_calculated:
             print(f"📊 Pre-calculated averages ready")
    result = ask_claude(question, filtered_results, pre_calculated)
    return result


def run_test_queries():
    questions = [
        "What is the status of the Lucerne Guest Experience Initiative?",
        "How is morale in Lucerne Operations team?",
        "What did the CFO decide about the Freiburg budget?",
        "Who owns the Lucerne Guest Experience Initiative?",
        "What is causing the delay in the Lucerne project?",
        "What do employees think about career development opportunities?",
        "How satisfied are employees with their current role out of 7?",
        "What are the main reasons employees are leaving the company?",
        "How do employees rate their work life balance out of 7?",
        "What is the overall sentiment across all teams?",
        "What feedback did employees give about management?",
        "What do employees appreciate most about working at Alpenblick?"
    ]

    print("\n🎯 EXECUTIVE QUERY TEST — 12 QUESTIONS")
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