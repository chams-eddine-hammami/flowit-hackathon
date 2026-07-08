# Query Engine
# Executive asks a question — Claude finds the answer with evidence
# Priority 0: Benny's real text survey answers
# Priority 1: Operational docs (chat, email, documents)
# Priority 2: Other survey content
# Priority 3: Exit interviews

import anthropic
import json
import os
import re
from dotenv import load_dotenv
from normalization.database import get_connection
from governance.access_control import filter_results_by_role, get_allowed_sources

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─── KEYWORD EXPANSIONS ──────────────────────────────────────
KEYWORD_EXPANSIONS = {
    "career": [
        "career", "advancement", "promotion", "growth",
        "progression", "professional development",
        "employee growth", "internal growth", "career path",
        "career opportunities", "career development",
        "career advancement", "career planning"
    ],
    "development": [
        "development", "training", "learning", "education",
        "upskilling", "professional development",
        "company investment", "employee growth",
        "training and development", "further education",
        "skill development", "learning opportunities"
    ],
    "morale": [
        "morale", "wellbeing", "satisfaction", "motivation",
        "engagement", "work environment", "team atmosphere",
        "employee morale", "team spirit", "workplace culture",
        "job satisfaction", "employee happiness"
    ],
    "workload": [
        "workload", "overload", "capacity", "stress", "burnout",
        "peak hours", "pressure", "task distribution",
        "work pressure", "overtime", "understaffed",
        "too much work", "resource constraints"
    ],
    "leaving": [
        "leaving", "resignation", "turnover", "exit",
        "departure", "termination", "attrition",
        "quit", "leaving company", "new job",
        "job change", "career transition"
    ],
    "sentiment": [
        "sentiment", "morale", "satisfaction", "engagement",
        "culture", "work environment", "employee experience",
        "workplace atmosphere", "team dynamics",
        "employee sentiment", "staff feeling"
    ],
    "management": [
        "management", "leadership", "supervisor", "manager",
        "feedback", "direct manager", "team lead",
        "management style", "leadership behavior",
        "manager support", "supervisor feedback"
    ],
    "communication": [
        "communication", "transparency", "information",
        "feedback", "internal communication",
        "company communication", "management communication",
        "information sharing", "strategic communication"
    ],
    "salary": [
        "salary", "compensation", "pay", "benefits", "wages",
        "remuneration", "financial compensation",
        "pay scale", "salary satisfaction"
    ],
    "satisfied": [
        "satisfied", "satisfaction", "happy", "content",
        "engagement", "job satisfaction", "role satisfaction",
        "work satisfaction", "employee satisfaction"
    ],
    "feedback": [
        "feedback", "review", "evaluation", "assessment",
        "recognition", "performance review",
        "employee feedback", "manager feedback"
    ],
    "teamwork": [
        "teamwork", "collaboration", "team", "colleagues",
        "cooperation", "team collaboration", "team dynamics",
        "working together", "cross-team", "interdepartmental"
    ],
    "balance": [
        "balance", "workload", "hours", "flexibility",
        "wellbeing", "work-life balance", "life balance",
        "flexible working", "work hours", "personal time"
    ],
    "trust": [
        "trust", "autonomy", "independence", "empowerment",
        "leadership", "leadership trust", "trust in management",
        "company trust", "organizational trust"
    ],
    "training": [
        "training", "development", "learning", "courses",
        "education", "training support", "further education",
        "professional training", "skill training",
        "training opportunities", "training program"
    ],
    "appreciation": [
        "appreciation", "recognition", "valued", "acknowledged",
        "reward", "employee recognition", "feeling valued",
        "acknowledgment", "praise", "positive feedback"
    ],
    "score": [
        "score", "rating", "scale", "satisfaction", "satisfied",
        "out of 7", "survey score", "employee score"
    ],
    "average": [
        "average", "mean", "score", "rating", "overall",
        "average score", "overall score", "mean score"
    ],
    "rate": [
        "rate", "rating", "score", "scale", "satisfied",
        "how do employees rate", "employee rating"
    ],
    "risk": [
        "risk", "attrition", "turnover", "resignation",
        "people risk", "retention risk", "talent risk",
        "employee risk", "hr risk"
    ],
    "retention": [
        "retention", "attrition", "turnover", "keeping employees",
        "employee retention", "staff retention",
        "talent retention", "reduce turnover"
    ],
    "culture": [
        "culture", "company culture", "workplace culture",
        "organizational culture", "team culture",
        "work environment", "values", "company values"
    ],
    "performance": [
        "performance", "productivity", "efficiency",
        "employee performance", "team performance",
        "performance review", "performance score"
    ],
    "jira": [
        "jira", "ticket", "alps", "frbs", "issue",
        "task", "hr-301", "project ticket", "open ticket"
    ],
    "ticket": [
        "ticket", "jira", "alps", "frbs", "issue",
        "task", "blocked", "done", "in progress", "open"
    ],
    "renovation": [
        "renovation", "freiburg", "panorama", "resort",
        "construction", "refurbishment", "upgrade"
    ],
    "initiative": [
        "initiative", "project", "lucerne", "guest experience",
        "check-in", "digital", "modernization"
    ],
    "legacy": [
        "legacy", "oracle", "hms", "old system",
        "api", "integration", "wrapper", "system fix"
    ],
    "improve": [
        "improve", "suggestion", "recommend", "better",
        "change", "improvement", "enhancement", "wish",
        "would like", "could do", "should do"
    ],
    "appreciate": [
        "appreciate", "like", "enjoy", "positive",
        "good", "great", "love", "value", "best"
    ]
}

SCORE_KEYWORDS = [
    'score', 'rating', 'scale', 'out of', 'average',
    'rate', 'how much', 'points', 'satisfied', 'satisfaction',
    'recommend', 'motivated', 'balance', 'manager',
    'leadership', 'workspace'
]

FINANCIAL_KEYWORDS = [
    'budget', 'cost', 'approved', 'eur', 'financial',
    'money', 'spend', 'investment', 'price', 'amount'
]

TEAM_KEYWORDS = [
    'how many', 'headcount', 'number of employees',
    'how many employees', 'team size', 'how many people',
    'employees in', 'staff in', 'members', 'how many staff'
]


def is_score_question(question: str) -> bool:
    return any(kw in question.lower() for kw in SCORE_KEYWORDS)


def is_financial_question(question: str) -> bool:
    return any(kw in question.lower() for kw in FINANCIAL_KEYWORDS)


def is_team_count_question(question: str) -> bool:
    return any(kw in question.lower() for kw in TEAM_KEYWORDS)


def expand_keywords(question: str) -> list:
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
    arabic = any('\u0600' <= c <= '\u06ff' for c in text)
    japanese = any('\u3040' <= c <= '\u30ff' for c in text)
    korean = any('\uac00' <= c <= '\ud7a3' for c in text)
    special = any(
        c.lower() in 'àáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿäöüß'
        for c in text
    )
    return arabic or japanese or korean or special


def translate_text(text: str) -> str:
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
    """Calculate ALL survey averages at once."""
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


def get_team_stats() -> str:
    """Calculate team headcount from survey data."""
    try:
        import pandas as pd
        df = pd.read_csv(
            'data/structured/alpenblick_hospitality_export_enriched.csv'
        )
        df['teams'] = df['teams'].astype(str)

        team_map = {
            'Lucerne Grand Hotel': 0,
            'Lucerne Operations': 0,
            'Lucerne Guest-Facing Services': 0,
            'Freiburg Operations': 0,
            'Freiburg Panorama Resort': 0,
            'Freiburg Guest-Facing Services': 0
        }

        unique_employees = df.drop_duplicates('respondent_id')
        for _, row in unique_employees.iterrows():
            teams_str = str(row['teams'])
            for team in team_map:
                words = team.split()
                if all(w in teams_str for w in words[:2]):
                    team_map[team] += 1

        result = "TEAM HEADCOUNT (survey participants):\n"
        for team, count in team_map.items():
            if count > 0:
                result += f"  {team}: {count} employees\n"
        result += f"  Total unique employees surveyed: {unique_employees.shape[0]}"
        return result
    except Exception:
        return None


def get_employee_info(question: str) -> str:
    """Look up employee team directly from survey CSV."""
    try:
        import pandas as pd
        id_match = re.search(r'6687\d+|2618\d+', question)
        if not id_match:
            return None

        emp_id = int(id_match.group())
        df = pd.read_csv(
            'data/structured/alpenblick_hospitality_export_enriched.csv'
        )
        emp_data = df[df['respondent_id'] == emp_id]

        if emp_data.empty:
            return f"Employee #{emp_id}: Not found in survey data."

        teams_raw = emp_data['teams'].iloc[0]
        total_responses = len(emp_data)
        surveys = emp_data['questionnaire_title'].unique().tolist()
        gender = emp_data['gender'].iloc[0] \
            if 'gender' in emp_data.columns else 'Unknown'
        start_date = emp_data['start_date'].iloc[0] \
            if 'start_date' in emp_data.columns else 'Unknown'

        return (
            f"EMPLOYEE PROFILE — #{emp_id}:\n"
            f"  Teams: {teams_raw}\n"
            f"  Gender: {gender}\n"
            f"  Start date: {start_date}\n"
            f"  Survey responses: {total_responses}\n"
            f"  Participated in: {', '.join([str(s) for s in surveys])}"
        )
    except Exception:
        return None


def ask_claude(question: str, context_docs: list, pre_calculated: str = None) -> dict:
    context = ""
    evidence = []

    for i, doc in enumerate(context_docs[:5]):
        context += f"\n[SOURCE {i+1}]"
        context += f"\nType: {doc['source_type']}"
        context += f"\nFrom: {doc['author_email']}"
        context += f"\nDate: {doc['timestamp']}"
        context += f"\nContent: {doc['content'][:500]}"
        context += "\n---"

        full_content = doc['content']
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
1. Answer ONLY from documents that DIRECTLY answer the question.
2. IGNORE any document not directly about the question topic.
3. Be direct — 2-3 sentences maximum.
4. All languages understood — respond in ENGLISH only.
5. Mention cross-language patterns when relevant.
6. Distinguish current employees from departing employees.

CONFIDENCE RULES:
- HIGH: 3+ directly relevant sources confirm the answer
- MEDIUM: 1-2 sources or partial information
- LOW: No relevant sources or very uncertain

EVIDENCE RULES:
- Only cite documents that DIRECTLY answer the question
- Better to show 1 relevant source than 5 irrelevant ones

HALLUCINATION RULES:
- If you have no evidence — say "I found no evidence for this."
- NEVER invent facts not in the documents

{f'''
‼️ PRE-CALCULATED DATA — USE THIS FIRST:
{pre_calculated}
''' if pre_calculated else ''}

QUESTION: {question}

DOCUMENTS:
{context}

Respond ONLY with valid JSON:
{{
    "answer": "2-3 sentence direct answer",
    "confidence": "high or medium or low",
    "key_finding": "single most important insight",
    "action_needed": "specific action or null",
    "uncertainty": "what is unclear or null",
    "relevant_sources": [1, 2, 3]
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

        relevant_indices = result.pop("relevant_sources", [])
        answer_lower = result.get("answer", "").lower()

        no_evidence_signals = [
            "found no evidence", "no evidence",
            "not available", "no relevant", "no data"
        ]
        if any(s in answer_lower for s in no_evidence_signals):
            result["evidence"] = []
        elif relevant_indices:
            relevant_evidence = []
            for idx in relevant_indices:
                if 1 <= idx <= len(evidence):
                    relevant_evidence.append(evidence[idx - 1])
            result["evidence"] = relevant_evidence if relevant_evidence else []
        else:
            result["evidence"] = evidence[:3]

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

    # Step 0a — Benny's text answers by TOPICS
    cursor.execute(f"""
        SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        INNER JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND r.author_email LIKE 'respondent_6687%'
        AND r.content NOT LIKE '%Score:%'
        AND ({where_topics})
        ORDER BY r.timestamp DESC
        LIMIT 5
    """, params_topics)
    benny_topics = cursor.fetchall()

    # Step 0b — Benny's text answers by CONTENT directly
    cursor.execute(f"""
        SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND r.author_email LIKE 'respondent_6687%'
        AND r.content NOT LIKE '%Score:%'
        AND ({where_content})
        ORDER BY r.timestamp DESC
        LIMIT 8
    """, params_content)
    benny_content = cursor.fetchall()

    # Combine Benny results
    benny_seen = set()
    benny_text = []
    for doc in list(benny_topics) + list(benny_content):
        if doc['id'] not in benny_seen:
            benny_seen.add(doc['id'])
            benny_text.append(doc)

    print(f"📊 Benny text answers: {len(benny_text)}")

    # Step 1 — Operational docs
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

    # Step 2 — Survey by content
    cursor.execute(f"""
        SELECT r.id, r.source_system, r.source_type,
               r.author_email, r.timestamp, r.content,
               r.metadata, e.sentiment, e.people_mentioned,
               e.projects_mentioned, e.decisions, e.key_topics
        FROM raw_documents r
        LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
        WHERE r.source_type = 'survey'
        AND r.content NOT LIKE '%Score:%'
        AND ({where_content})
        ORDER BY r.timestamp DESC
        LIMIT 5
    """, params_content)
    surveys_content = cursor.fetchall()

    # Step 3 — Survey by topics (all including scores)
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
        LIMIT 10
    """, params_topics)
    surveys_topics = cursor.fetchall()

    conn.close()

    # ── COMBINE — STRICT PRIORITY ─────────────────────────────
    seen = set()
    all_results = []

    # PRIORITY 0 — Benny's real text answers FIRST
    for doc in list(benny_text):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # PRIORITY 1 — Operational docs
    for doc in list(unstructured):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # PRIORITY 2 — Other survey content
    for doc in list(surveys_content):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # PRIORITY 3 — Exit interviews (max 2)
    exit_count = 0
    for doc in list(surveys_topics):
        if doc['id'] not in seen:
            author = doc['author_email'] or ''
            if 'respondent_2' in author and exit_count < 2:
                seen.add(doc['id'])
                all_results.append(doc)
                exit_count += 1

    # PRIORITY 4 — anything remaining
    for doc in list(surveys_topics):
        if doc['id'] not in seen:
            seen.add(doc['id'])
            all_results.append(doc)

    # Governance
    filtered_results = filter_results_by_role(all_results, role)

    # Financial filter
    if is_financial_question(question):
        financial_docs = [
            d for d in filtered_results
            if d['source_type'] in ('email', 'document', 'chat_messaging')
            and any(kw in d['content'].lower()
                   for kw in ['budget', 'eur', 'approved', 'cost'])
        ]
        if financial_docs:
            filtered_results = financial_docs

    # Deduplicate
    seen_content = set()
    unique_results = []
    for doc in filtered_results:
        content_key = doc['content'][:100]
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_results.append(doc)
    filtered_results = unique_results

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

    # Pre-calculated data
    pre_calculated = None

    # Employee lookup
    emp_info = get_employee_info(question)
    if emp_info:
        pre_calculated = emp_info
        id_match = re.search(r'6687\d+|2618\d+', question)
        if id_match:
            emp_id = id_match.group()
            from normalization.database import get_connection as get_conn
            emp_conn = get_conn()
            emp_cursor = emp_conn.cursor()
            emp_cursor.execute("""
                SELECT r.id, r.source_system, r.source_type,
                       r.author_email, r.timestamp, r.content,
                       r.metadata, e.sentiment, e.people_mentioned,
                       e.projects_mentioned, e.decisions, e.key_topics
                FROM raw_documents r
                LEFT JOIN enriched_documents e ON r.id = e.raw_document_id
                WHERE r.author_email LIKE ?
                AND r.source_type = 'survey'
                AND r.metadata LIKE '%teams%'
                LIMIT 3
            """, (f"%{emp_id}%",))
            emp_survey_docs = emp_cursor.fetchall()
            emp_conn.close()
            if emp_survey_docs:
                filtered_results = list(emp_survey_docs)

    # Team headcount
    if is_team_count_question(question):
        team_stats = get_team_stats()
        if team_stats:
            pre_calculated = (
                team_stats if not pre_calculated
                else pre_calculated + '\n\n' + team_stats
            )

    # Score averages
    if is_score_question(question):
        averages = get_all_averages()
        if averages:
            pre_calculated = (
                averages if not pre_calculated
                else pre_calculated + '\n\n' + averages
            )

    print(f"✅ Final: {len(filtered_results)} documents")
    print(f"📊 Benny first: {len(benny_text)} text answers")

    result = ask_claude(question, filtered_results, pre_calculated)

    # Safety check
    if result is None:
        result = {
            "answer": "Could not process this question.",
            "confidence": "low",
            "key_finding": "System error",
            "action_needed": None,
            "uncertainty": None,
            "evidence": []
        }

    # Clean response when no data
    no_data_signals = [
        'no relevant information',
        'cannot find any information',
        'not available in any connected',
        'no documents contain',
    ]
    answer_lower = result.get('answer', '').lower()
    if any(signal in answer_lower for signal in no_data_signals):
        result['evidence'] = []
        result['confidence'] = 'low'
        result['answer'] = (
            "This information is not available in any connected source. "
            "The question may require a data source that is not yet connected."
        )
        result['key_finding'] = "Data not available in current connected sources."
        result['action_needed'] = (
            "Consider connecting the relevant data source "
            "to answer this type of question."
        )
        result['uncertainty'] = None

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
        "What improvements do employees suggest for the company?",
        "How many employees work in Freiburg Operations?"
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