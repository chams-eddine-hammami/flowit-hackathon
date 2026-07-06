# Flowit Intelligence Platform
# Mobile-first executive chat interface
# Built with Streamlit — runs in phone browser

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_layer.query_engine import query
from governance.access_control import get_allowed_sources
from governance.audit_log import init_audit_table, log_access

# ─── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="Flowit Intelligence",
    page_icon="🏨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── STYLING ─────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {
        max-width: 500px !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .stTextInput input {
        border-radius: 25px;
        padding: 12px 20px;
        font-size: 16px;
        border: 2px solid #e0e0e0;
    }
    .stButton button {
        border-radius: 25px;
        background-color: #2563EB;
        color: white;
        font-size: 16px;
        padding: 10px 24px;
        border: none;
        width: 100%;
    }
    .stButton button:hover { background-color: #1d4ed8; }
    .answer-card {
        background: #f0f7ff;
        border-left: 4px solid #2563EB;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        color: #1a1a1a;
    }
    .user-bubble {
        background: #2563EB;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 8px 0;
        text-align: right;
        font-size: 15px;
    }
    .assistant-bubble {
        background: #f0f0f0;
        color: #1a1a1a;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 15px;
    }
    .badge-high {
        color: #16a34a !important;
        font-weight: bold;
        background: #dcfce7;
        padding: 3px 10px;
        border-radius: 12px;
    }
    .badge-medium {
        color: #d97706 !important;
        font-weight: bold;
        background: #fef3c7;
        padding: 3px 10px;
        border-radius: 12px;
    }
    .badge-low {
        color: #dc2626 !important;
        font-weight: bold;
        background: #fee2e2;
        padding: 3px 10px;
        border-radius: 12px;
    }
    .stInfo {
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
    .streamlit-expanderHeader {
        font-size: 13px !important;
        color: #2563EB !important;
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


# ─── LOGIN ────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style='text-align:center; padding:20px 0 10px 0;
                border-bottom:1px solid #e0e0e0; margin-bottom:20px;'>
        <h1>🏨 Flowit Intelligence</h1>
        <p style='color:#666; font-size:14px;'>
            Connected intelligence for Alpenblick Hospitality
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Welcome back")
    st.markdown("Sign in to access your intelligence dashboard.")

    name = st.text_input("Your name", placeholder="e.g. Sarah Miller")
    role = st.selectbox("Your role", [
        "Select your role...",
        "CEO — Full Access",
        "CFO — Finance & Operations",
        "HR Manager — People & Surveys",
        "Operations Manager — Teams & Projects"
    ])

    if st.button("Sign In →"):
        if name and role != "Select your role...":
            st.session_state.logged_in = True
            st.session_state.name = name
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Please enter your name and select your role.")


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

    with st.spinner("Searching all sources..."):
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
    """Clean professional evidence card with number."""

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

    # Clean content — remove technical suffixes
    if 'Q:' in content and '| A:' in content:
        parts = content.split('| A:')
        question_part = parts[0].replace('Q:', '').strip()
        if '| Score:' in question_part:
            question_part = question_part.split('| Score:')[0].strip()
        answer_part = parts[1].strip() if len(parts) > 1 else content
        if '| Type:' in answer_part:
            answer_part = answer_part.split('| Type:')[0].strip()
        if '| Score:' in answer_part:
            answer_part = answer_part.split('| Score:')[0].strip()
    else:
        question_part = None
        answer_part = content

    # Evidence header
    st.markdown(f"""
    <div style='background:#f8fafc; border-radius:10px;
                padding:12px 14px; margin:12px 0 6px 0;
                border-left:4px solid #2563EB;'>
        <p style='margin:0 0 4px 0; font-size:13px;
                  font-weight:700; color:#2563EB;'>
            📌 Evidence #{number}
        </p>
        <p style='margin:0; font-size:12px; color:#64748b; line-height:1.8;'>
            {source_emoji} <strong>Source:</strong> {source_label}<br>
            📅 <strong>Date:</strong> {date_display}<br>
            👤 <strong>From:</strong> {author_display}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Question if exists
    if question_part:
        st.markdown(
            f"<p style='color:#64748b; font-size:12px; "
            f"font-style:italic; margin:4px 0 6px 8px;'>"
            f"❓ {question_part}</p>",
            unsafe_allow_html=True
        )

    # Answer
    st.markdown(
        f"<div style='background:white; border-radius:8px; "
        f"padding:10px 14px; margin:0 0 8px 0; "
        f"border:1px solid #e2e8f0;'>"
        f"<p style='margin:0; color:#1e293b; font-size:13px; "
        f"line-height:1.7;'>{answer_part}</p>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Translation
    translation = e.get('translation')
    if translation:
        st.markdown(
            f"<div style='background:#f0fdf4; border-radius:8px; "
            f"padding:8px 14px; margin:0 0 8px 0;'>"
            f"<p style='margin:0; color:#166534; font-size:12px;'>"
            f"🇬🇧 <strong>English:</strong> {translation}</p>"
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

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <div style='padding:10px 0;'>
            <strong>🏨 Flowit Intelligence</strong><br>
            <small style='color:#666;'>{emoji} {st.session_state.name}
            · {st.session_state.role}</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Sign out"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.rerun()

    # Access badge
    allowed = get_allowed_sources(st.session_state.role)
    source_labels = {
        'chat_messaging': '💬 Chat',
        'email': '📧 Email',
        'document': '📄 Docs',
        'survey': '📊 Surveys'
    }
    access_text = " · ".join([source_labels.get(s, s) for s in allowed])
    st.markdown(f"""
    <div style='background:#f0f7ff; border-radius:8px;
                padding:8px 12px; margin:4px 0;
                font-size:12px; color:#1a1a1a;'>
        🔐 <strong>Your access:</strong> {access_text}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Suggestions
    if not st.session_state.chat_history:
        st.markdown("**💡 Try asking:**")
        suggestions = [
            "What is the status of the Lucerne initiative?",
            "How is morale in Lucerne Operations?",
            "Why are employees leaving?",
            "What is the average satisfaction score?",
            "What do employees think about career development?"
        ]
        for suggestion in suggestions:
            if st.button(f"→ {suggestion}", key=suggestion):
                process_question(suggestion)
                st.rerun()
        st.divider()

    # Chat history
    for chat in st.session_state.chat_history:
        # User bubble
        st.markdown(
            f"<div class='user-bubble'>{chat['question']}</div>",
            unsafe_allow_html=True
        )

        result = chat['result']
        confidence = result.get('confidence', 'low')
        badge_class = f"badge-{confidence}"

        # Answer bubble
        st.markdown(
            f"<div class='assistant-bubble'>{result['answer']}</div>",
            unsafe_allow_html=True
        )

        # Key finding
        if result.get('key_finding'):
            st.markdown(f"""
            <div class='answer-card'>
                ⚡ <strong>Key finding:</strong> {result['key_finding']}
                <br><br>
                <span class='{badge_class}'>
                    ● {confidence.upper()} CONFIDENCE
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Action needed
        if result.get('action_needed'):
            st.markdown(f"""
            <div style='background:#fff7ed; border-left:4px solid #f97316;
                        border-radius:8px; padding:12px; margin:6px 0;
                        color:#1a1a1a;'>
                🎯 <strong>Action needed:</strong> {result['action_needed']}
            </div>
            """, unsafe_allow_html=True)

        # Uncertainty
        if result.get('uncertainty'):
            st.markdown(f"""
            <div style='background:#fafafa; border-radius:8px;
                        padding:10px; margin:6px 0;
                        border:1px solid #e0e0e0;'>
                <span style='color:#555; font-size:13px;'>
                ⚠️ <em>{result['uncertainty']}</em></span>
            </div>
            """, unsafe_allow_html=True)

        # Evidence — smart display
        if result.get('evidence'):
            evidence_list = result['evidence']
            with st.expander(
                f"📎 View evidence ({len(evidence_list)} sources)"
            ):
                for idx, ev in enumerate(evidence_list):
                    render_evidence_card(ev, idx + 1)

        st.divider()

    # Input
    st.markdown("**Ask anything about your teams, projects, or people:**")
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "",
            placeholder="e.g. How is the Lucerne team doing?",
            label_visibility="collapsed",
            key="question_input"
        )
    with col2:
        send = st.button("Send")

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