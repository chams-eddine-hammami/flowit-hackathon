# Flowit Intelligence Platform
# Mobile-first executive chat interface

import streamlit as st
import sys
import os
import base64
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_layer.query_engine import query
from governance.access_control import get_allowed_sources
from governance.audit_log import init_audit_table, log_access

st.set_page_config(
    page_title="flowit AI",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background: #f0f4f8; }
    .block-container {
        max-width: 420px !important;
        padding: 0.5rem 1rem !important;
    }
    /* Input */
    .stTextInput input {
        background: white !important;
        border: 1.5px solid #d1d5db !important;
        color: #111827 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 15px !important;
    }
    .stTextInput input::placeholder { color: #9ca3af !important; }
    /* Select */
    .stSelectbox > div > div {
        background: white !important;
        border: 1.5px solid #d1d5db !important;
        border-radius: 10px !important;
        color: #111827 !important;
    }
    /* ALL Buttons */
    .stButton button {
        background: #1a3a6b !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border: none !important;
        width: 100% !important;
    }
    .stButton button:hover {
        background: #142d54 !important;
        color: white !important;
    }
    /* Labels */
    label { color: #374151 !important; font-size: 13px !important; }
    /* Divider */
    hr { border-color: #d1d5db !important; margin: 12px 0 !important; }
    /* Chat bubbles */
    .user-bubble {
        background: #1a3a6b;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 8px 0;
        text-align: right;
        font-size: 15px;
    }
    .assistant-bubble {
        background: white;
        color: #111827;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .answer-card {
        background: #eff6ff;
        border-left: 4px solid #1a3a6b;
        border-radius: 10px;
        padding: 16px;
        margin: 10px 0;
        color: #111827;
    }
    .badge-high {
        color: #166534 !important;
        font-weight: 700;
        background: #dcfce7;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
    }
    .badge-medium {
        color: #92400e !important;
        font-weight: 700;
        background: #fef3c7;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
    }
    .badge-low {
        color: #991b1b !important;
        font-weight: 700;
        background: #fee2e2;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
    }
    /* Spinner */
    .stSpinner > div { border-top-color: #1a3a6b !important; }
    /* Expander */
    .streamlit-expanderHeader {
        background: white !important;
        color: #374151 !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
    }
    /* Evidence cards */
    .evidence-header {
        background: white;
        border-radius: 10px;
        padding: 12px 14px;
        margin: 10px 0 6px 0;
        border-left: 4px solid #1a3a6b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
     /* Expander header — dark text */
    .streamlit-expanderHeader p {
        color: #111827 !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderHeader {
        color: #111827 !important;
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
    }
    details summary {
        color: #111827 !important;
    }
    details summary p {
        color: #111827 !important;
    }
    [data-testid="stExpander"] summary {
        color: #111827 !important;
        background: white !important;
    }
    [data-testid="stExpander"] summary span {
        color: #111827 !important;
    }
            
    /* Spinner text — dark */
    .stSpinner p {
        color: #111827 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stSpinner"] p {
        color: #111827 !important;
    }
            
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "name" not in st.session_state:
    st.session_state.name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ─── LOGO ─────────────────────────────────────────────────────
def get_logo():
    logo_path = Path("interface/flowit_logo.jpeg")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return (
            f'<img src="data:image/jpeg;base64,{data}" '
            f'style="width:52px; height:52px; border-radius:10px; '
            f'margin-bottom:10px; object-fit:contain;">'
        )
    return '<div style="font-size:40px; margin-bottom:10px;">✦</div>'


# ─── LOGIN ────────────────────────────────────────────────────
def show_login():
    st.markdown("<br>", unsafe_allow_html=True)

    logo_html = get_logo()
    st.markdown(f"""
    <div style='text-align:center; padding:20px 0 16px 0;'>
        {logo_html}
        <h1 style='font-size:24px; font-weight:700;
                   color:#1a3a6b; margin:0 0 6px 0;'>
            flowit AI
        </h1>
        <p style='color:#6b7280; font-size:13px; margin:0;'>
            Connected intelligence from your people data
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    name = st.text_input("Full name", placeholder="e.g. Anna Schmidt")

    role = st.selectbox("Your role", [
        "Select your role...",
        "CEO — Full Access",
        "CFO — Finance & Operations",
        "HR Manager — People & Surveys",
        "Operations Manager — Teams & Projects"
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Sign In →"):
        if name and role != "Select your role...":
            st.session_state.logged_in = True
            st.session_state.name = name
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Please enter your name and select your role.")

    st.markdown("""
    <p style='text-align:center; color:#9ca3af; font-size:11px; margin-top:28px;'>
        🔒 Privacy-first · Swiss-made · Powered by Flowit AI
    </p>
    """, unsafe_allow_html=True)


# ─── PROCESS QUESTION ─────────────────────────────────────────
def process_question(question: str):
    from governance.access_control import is_question_allowed
    if not is_question_allowed(st.session_state.role, question):
        st.session_state.chat_history.append({
            "question": question,
            "result": {
                "answer": "🔒 Access denied. You do not have permission to access this information.",
                "confidence": "high",
                "key_finding": "This topic is restricted for your role.",
                "action_needed": "Contact your administrator if you need access.",
                "uncertainty": None,
                "evidence": [],
                "access_denied": True
            }
        })
        return

    with st.spinner("🔍 Searching all sources..."):
        result = query(question, role=st.session_state.role)

    sources = [e['type'] for e in result.get('evidence', [])]
    log_access(
        user_name=st.session_state.name,
        user_role=st.session_state.role,
        question=question,
        sources_accessed=sources,
        confidence=result.get('confidence', 'unknown')
    )

    st.session_state.chat_history.append({
        "question": question,
        "result": result
    })


# ─── EVIDENCE CARD ────────────────────────────────────────────
def render_evidence_card(e: dict, number: int):
    source_label = {
        'chat_messaging': 'Chat Message',
        'email': 'Email',
        'document': 'Document',
        'survey': 'Employee Survey',
        'jira_tickets': 'Jira Ticket',
        'slack_chat': 'Slack Message',
        'sharepoint_files': 'SharePoint File',
        'meeting_notes': 'Meeting Notes',
        'legacy_hr_system': 'HR System Record'
    }.get(e['source'], e['type'].replace('_', ' ').title())

    source_emoji = {
        'chat_messaging': '💬',
        'email': '📧',
        'document': '📄',
        'survey': '📊',
        'jira_tickets': '🎫',
        'slack_chat': '💬',
        'sharepoint_files': '🗂️',
        'meeting_notes': '📝',
        'legacy_hr_system': '🏢'
    }.get(e['source'], '📌')

    author_display = (
        e['author']
        .replace('@alpenblick.com', '')
        .replace('respondent_', 'Employee #')
    )
    date_display = str(e['date'])[:10]
    content = e.get('preview', '')

   

        # Parse content based on format
    score_value = None
    question_part = None
    answer_part = content

    # Format 1: New survey format "Question:\n...\n\nAnswer:\n..."
    if 'Question:\n' in content and '\n\nAnswer:\n' in content:
        parts = content.split('\n\nAnswer:\n')
        question_part = parts[0].replace('Question:\n', '').strip()
        answer_part = parts[1].strip() if len(parts) > 1 else content
        if '\n\nTopics:' in answer_part:
            answer_part = answer_part.split('\n\nTopics:')[0].strip()
        if '\n\nKeywords:' in answer_part:
            answer_part = answer_part.split('\n\nKeywords:')[0].strip()
        answer_part = answer_part.replace('• ', '').strip()

    # Format 2: New score format "Question:\n...\n\nScore:\n..."
    elif 'Question:\n' in content and '\n\nScore:\n' in content:
        parts = content.split('\n\nScore:\n')
        question_part = parts[0].replace('Question:\n', '').strip()
        score_str = parts[1].strip().split('\n')[0] if len(parts) > 1 else ''
        try:
            score_value = float(score_str.split('/')[0].strip())
            answer_part = None
        except:
            answer_part = score_str

    # Format 3: Old format "Q: ... | Score: X out of 7"
    elif 'Q:' in content and 'Score:' in content and 'out of 7' in content:
        try:
            question_part = content.split('|')[0].replace('Q:', '').strip()
            score_str = content.split('Score:')[1].split('out of 7')[0].strip()
            score_value = float(score_str)
            answer_part = None
        except:
            pass

    # Format 4: Old format "Q: ... | A: ..."
    elif 'Q:' in content and '| A:' in content:
        parts = content.split('| A:')
        question_part = parts[0].replace('Q:', '').strip()
        answer_part = parts[1].strip() if len(parts) > 1 else content
        if '| Type:' in answer_part:
            answer_part = answer_part.split('| Type:')[0].strip()
        if '| Score:' in answer_part:
            answer_part = answer_part.split('| Score:')[0].strip()
        answer_part = answer_part.rstrip('| ').strip()

        # Clean Topics and Keywords nan from display
    if answer_part:
     answer_part = answer_part.replace('| Topics: nan', '')
     answer_part = answer_part.replace('| Keywords: nan', '')
     answer_part = answer_part.replace('Topics: nan', '')
     answer_part = answer_part.replace('Keywords: nan', '')
     answer_part = answer_part.strip().rstrip('|').strip()

    # Evidence header
    st.markdown(f"""
    <div style='background:white; border-radius:10px;
                padding:12px 14px; margin:10px 0 4px 0;
                border-left:4px solid #1a3a6b;
                box-shadow:0 1px 4px rgba(0,0,0,0.08);'>
        <p style='margin:0 0 4px 0; font-size:12px;
                  font-weight:700; color:#1a3a6b;'>
            📌 Evidence #{number}
        </p>
        <p style='margin:0; font-size:12px; color:#4b5563; line-height:1.8;'>
            {source_emoji} <strong>Source:</strong> {source_label}<br>
            📅 <strong>Date:</strong> {date_display}<br>
            👤 <strong>From:</strong> {author_display}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Score display
    if score_value is not None and question_part:
        score_color = (
            "#16a34a" if score_value >= 5
            else "#d97706" if score_value >= 3
            else "#dc2626"
        )
        score_pct = round((score_value / 7) * 100)
        st.markdown(f"""
        <div style='background:#f9fafb; border-radius:8px;
                    padding:12px 14px; margin:0 0 8px 0;
                    border:1px solid #e5e7eb;'>
            <p style='margin:0 0 4px 0; color:#6b7280;
                      font-size:12px; font-style:italic;'>
                ❓ {question_part}
            </p>
            <p style='margin:0 0 8px 0; color:#111827; font-size:14px;'>
                {author_display} rated
                <strong style='color:{score_color}; font-size:22px;'>
                {score_value:.0f}
                </strong>
                <span style='color:#6b7280;'> out of 7</span>
            </p>
            <div style='background:#e5e7eb; border-radius:10px; height:6px;'>
                <div style='background:{score_color}; width:{score_pct}%;
                            height:6px; border-radius:10px;'></div>
            </div>
            <p style='margin:3px 0 0 0; font-size:11px; color:#9ca3af;'>
                {score_pct}% of maximum
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    elif answer_part:
        if question_part:
            st.markdown(
                f"<p style='color:#6b7280; font-size:12px; "
                f"font-style:italic; margin:4px 0 4px 0;'>"
                f"❓ {question_part}</p>",
                unsafe_allow_html=True
            )
        st.markdown(
            f"<div style='background:#f8fafc; border-radius:8px; "
            f"padding:10px 14px; margin:0 0 8px 0; "
            f"border:1px solid #e5e7eb;'>"
            f"<p style='margin:0; color:#1a1a1a; font-size:13px; "
            f"line-height:1.7;'>{answer_part}</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    translation = e.get('translation')
    if translation:
        # Clean translation — remove question repetition
        clean_translation = translation
        if 'Question:' in translation:
            clean_translation = translation.split('Question:')[0].strip()
        if clean_translation:
            st.markdown(
                f"<div style='background:#f0fdf4; border-radius:8px; "
                f"padding:8px 14px; margin:0 0 8px 0; "
                f"border:1px solid #bbf7d0;'>"
                f"<p style='margin:0; color:#166534; font-size:12px;'>"
                f"🇬🇧 <strong>English translation:</strong></p>"
                f"<p style='margin:4px 0 0 0; color:#14532d; "
                f"font-size:13px; line-height:1.6;'>{clean_translation}</p>"
                f"</div>",
                unsafe_allow_html=True
            )


# ─── CHAT PAGE ────────────────────────────────────────────────
def show_chat():
    role_emoji = {
        "CEO — Full Access": "👔",
        "CFO — Finance & Operations": "💰",
        "HR Manager — People & Surveys": "👥",
        "Operations Manager — Teams & Projects": "⚙️"
    }
    emoji = role_emoji.get(st.session_state.role, "👤")

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div style='padding:8px 0;'>
            <strong style='color:#1a3a6b; font-size:16px;'>✦ flowit AI</strong><br>
            <small style='color:#6b7280; font-size:12px;'>
                {emoji} {st.session_state.name} · {st.session_state.role}
            </small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("↩"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.rerun()

    # Access badge
    allowed = get_allowed_sources(st.session_state.role)
    source_labels = {
        'chat_messaging': '💬 Chat · 💬 Slack',
        'email': '📧 Email',
        'document': '📄 Docs · 🗂️ SharePoint · 🎫 Jira · 📝 Meetings · 🏢 HR',
        'survey': '📊 Surveys'
    }
    access_text = " · ".join([source_labels.get(s, s) for s in allowed])

    st.markdown(f"""
    <div style='background:#eff6ff; border-radius:8px;
                padding:6px 12px; margin:4px 0 8px 0;
                font-size:11px; border:1px solid #bfdbfe;'>
        <span style='color:#1e40af;'>🔐 <strong>Access:</strong> {access_text}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Role-based suggestions
    if not st.session_state.chat_history:
        role_suggestions = {
            "CEO — Full Access": [
                "Why are employees leaving the company?",
                "Which project has the highest risk right now?",
                "What is the overall company morale?",
                "Summarize the Lucerne Guest Experience Initiative",
                "What are the biggest people risks at Alpenblick?"
            ],
            "CFO — Finance & Operations": [
                "What is the Freiburg expansion budget status?",
                "Which projects have financial risks?",
                "What did the CFO decide about the Freiburg renovation?",
                "What is the status of the Lucerne initiative?",
                "What are the open Jira tickets and their priorities?"
            ],
            "HR Manager — People & Surveys": [
                "What are the main employee complaints?",
                "What are the main reasons for resignation?",
                "What do employees think about career development?",
                "Which teams have the lowest satisfaction scores?",
                "Which teams have low engagement?"
            ],
            "Operations Manager — Teams & Projects": [
                "What operational issues exist right now?",
                "What are the current engineering blockers?",
                "What happened in the latest operations meeting?",
                "Which Jira issues are delayed or blocked?",
                "What is the status of the Lucerne initiative?"
            ]
        }
        suggestions = role_suggestions.get(st.session_state.role, [
            "What is the status of the Lucerne initiative?",
            "How is morale in Lucerne Operations?",
            "Why are employees leaving?",
            "What is the average satisfaction score?",
            "What do employees think about career development?"
        ])

        st.markdown(
            "<p style='color:#374151; font-size:13px; "
            "font-weight:600; margin-bottom:8px;'>💡 Try asking:</p>",
            unsafe_allow_html=True
        )
        for suggestion in suggestions:
            if st.button(f"→ {suggestion}", key=suggestion):
                process_question(suggestion)
                st.rerun()
        st.markdown("---")

    # Chat history
    for chat in st.session_state.chat_history:
        st.markdown(
            f"<div class='user-bubble'>{chat['question']}</div>",
            unsafe_allow_html=True
        )

        result = chat['result']
        confidence = result.get('confidence', 'low')
        badge_class = f"badge-{confidence}"

        st.markdown(
            f"<div class='assistant-bubble'>{result['answer']}</div>",
            unsafe_allow_html=True
        )

        if result.get('key_finding'):
            st.markdown(f"""
            <div class='answer-card'>
                ⚡ <strong style='color:#1a3a6b;'>Key finding:</strong>
                <span style='color:#111827;'> {result['key_finding']}</span>
                <br><br>
                <span class='{badge_class}'>
                    ● {confidence.upper()} CONFIDENCE
                </span>
            </div>
            """, unsafe_allow_html=True)

        if result.get('action_needed'):
            st.markdown(f"""
            <div style='background:#fff7ed; border-left:4px solid #f97316;
                        border-radius:8px; padding:12px; margin:6px 0;'>
                <span style='color:#c2410c;'>
                    🎯 <strong>Action needed:</strong>
                </span>
                <span style='color:#7c2d12;'> {result['action_needed']}</span>
            </div>
            """, unsafe_allow_html=True)

        if result.get('uncertainty'):
            st.markdown(f"""
            <div style='background:#f9fafb; border-radius:8px;
                        padding:10px; margin:6px 0;
                        border:1px solid #e5e7eb;'>
                <span style='color:#6b7280; font-size:13px;'>
                ⚠️ <em>{result['uncertainty']}</em></span>
            </div>
            """, unsafe_allow_html=True)

        if result.get('evidence'):
            evidence_list = result['evidence']
            with st.expander(
                f"📎 View evidence ({len(evidence_list)} sources)"
            ):
                for idx, ev in enumerate(evidence_list):
                    render_evidence_card(ev, idx + 1)

        st.markdown("---")

    # Input
    st.markdown(
        "<p style='color:#6b7280; font-size:12px; margin-bottom:6px;'>"
        "Ask anything about your teams, projects, or people:</p>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns([6, 1])
    with col1:
        question = st.text_input(
            "",
            placeholder="e.g. How is the Lucerne team doing?",
            label_visibility="collapsed",
            key="question_input"
        )
    with col2:
        send = st.button("→")

    if send and question:
        process_question(question)
        st.rerun()


# ─── MAIN ─────────────────────────────────────────────────────
def main():
    init_audit_table()
    if not st.session_state.logged_in:
        show_login()
    else:
        show_chat()


if __name__ == "__main__":
    main()