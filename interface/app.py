# Flowit Intelligence Platform
# Mobile-first executive chat interface
# Built with Streamlit — runs in phone browser

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_layer.query_engine import query
from normalization.database import get_connection
from governance.access_control import get_allowed_sources, filter_results_by_role, get_role_description
from governance.audit_log import init_audit_table, log_access, get_audit_log

# ─── PAGE CONFIG ────────────────────────────────────────────
st.set_page_config(
    page_title="Flowit Intelligence",
    page_icon="🏨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── MOBILE STYLING ─────────────────────────────────────────
st.markdown("""
<style>
    .main { max-width: 480px; margin: 0 auto; padding: 0 10px; }
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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE ───────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "name" not in st.session_state:
    st.session_state.name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ─── LOGIN PAGE ──────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style='text-align: center; padding: 20px 0 10px 0;
                border-bottom: 1px solid #e0e0e0; margin-bottom: 20px;'>
        <h1>🏨 Flowit Intelligence</h1>
        <p style='color: #666; font-size: 14px;'>
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


# ─── PROCESS QUESTION ────────────────────────────────────────
def process_question(question: str):
    """Query the AI and store result in chat history."""

    # Check if question is allowed for this role BEFORE querying
    from governance.access_control import is_question_allowed
    if not is_question_allowed(st.session_state.role, question):
        st.session_state.chat_history.append({
            "question": question,
            "result": {
                "answer": "🔒 Access denied. You do not have permission to access this information.",
                "confidence": "high",
                "key_finding": "This topic is restricted for your role.",
                "action_needed": "Contact your administrator if you need access to this data.",
                "uncertainty": None,
                "evidence": [],
                "access_denied": True
            }
        })
        return

    with st.spinner("Searching all sources..."):
        result = query(
            question,
            role=st.session_state.role
        )

    # Log every access — audit trail
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


# ─── CHAT PAGE ───────────────────────────────────────────────
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
        <div style='padding: 10px 0;'>
            <strong>🏨 Flowit Intelligence</strong><br>
            <small style='color: #666;'>{emoji} {st.session_state.name}
            · {st.session_state.role}</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Sign out"):
            st.session_state.logged_in = False
            st.session_state.chat_history = []
            st.rerun()

    # Show role permissions
    allowed = get_allowed_sources(st.session_state.role)
    source_labels = {
        'chat_messaging': '💬 Chat',
        'email': '📧 Email',
        'document': '📄 Documents',
        'survey': '📊 Surveys'
    }
    access_text = " · ".join([source_labels.get(s, s) for s in allowed])
    st.markdown(f"""
    <div style='background: #f0f7ff; border-radius: 8px;
                padding: 8px 12px; margin: 4px 0;
                font-size: 12px; color: #1a1a1a;'>
        🔐 <strong style='color: #1a1a1a;'>Your access:</strong>
        <span style='color: #1a1a1a;'>{access_text}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown("**💡 Try asking:**")

        suggestions = [
            "What is the status of the Lucerne initiative?",
            "How is morale in Lucerne Operations?",
            "Why are employees leaving?",
            "What did the CFO decide about Freiburg?",
            "What is the overall team sentiment?"
        ]

        for suggestion in suggestions:
            if st.button(f"→ {suggestion}", key=suggestion):
                process_question(suggestion)
                st.rerun()

        st.divider()

    # Chat history
    for chat in st.session_state.chat_history:
        st.markdown(f"""
        <div class='user-bubble'>{chat['question']}</div>
        """, unsafe_allow_html=True)

        result = chat['result']
        confidence = result.get('confidence', 'low')
        badge_class = f"badge-{confidence}"

        st.markdown(f"""
        <div class='assistant-bubble'>{result['answer']}</div>
        """, unsafe_allow_html=True)

        if result.get('key_finding'):
            st.markdown(f"""
            <div class='answer-card'>
                ⚡ <strong style='color: #1a1a1a;'>Key finding:</strong>
                <span style='color: #1a1a1a;'>{result['key_finding']}</span>
                <br><br>
                <span class='{badge_class}'>● {confidence.upper()} CONFIDENCE</span>
            </div>
            """, unsafe_allow_html=True)

        if result.get('action_needed'):
            st.markdown(f"""
            <div style='background: #fff7ed; border-left: 4px solid #f97316;
                        border-radius: 8px; padding: 12px; margin: 6px 0;
                        color: #1a1a1a;'>
                🎯 <strong style='color: #1a1a1a;'>Action needed:</strong>
                <span style='color: #1a1a1a;'>{result['action_needed']}</span>
            </div>
            """, unsafe_allow_html=True)

        if result.get('uncertainty'):
            st.markdown(f"""
            <div style='background: #fafafa; border-radius: 8px;
                        padding: 10px; margin: 6px 0;
                        border: 1px solid #e0e0e0;'>
                <span style='color: #555555; font-size: 13px;'>
                ⚠️ <em>{result['uncertainty']}</em></span>
            </div>
            """, unsafe_allow_html=True)

        if result.get('evidence'):
            with st.expander(
                f"📎 View evidence ({len(result['evidence'])} sources)"
            ):
                for e in result['evidence']:
                    source_emoji = {
                        'chat_messaging': '💬',
                        'email': '📧',
                        'document': '📄',
                        'survey': '📊'
                    }.get(e['type'], '📌')

                    source_label = {
                        'chat_messaging': 'Teams / Chat Message',
                        'email': 'Email',
                        'document': 'Document',
                        'survey': 'Alpenblick Survey Data'
                    }.get(e['type'], 'Unknown Source')

                    st.markdown(f"""
                    <div style='background: #ffffff;
                                border: 1px solid #e0e0e0;
                                border-radius: 8px; padding: 12px;
                                margin: 8px 0; color: #1a1a1a;'>
                        <p style='margin:0; color: #1a1a1a;'>
                            {source_emoji}
                            <strong style='color: #1a1a1a;'>Source:</strong>
                            <span style='color: #1a1a1a;'>{source_label}</span>
                        </p>
                        <p style='margin:4px 0; color: #1a1a1a;'>
                            👤 <strong style='color: #1a1a1a;'>From:</strong>
                            <span style='color: #1a1a1a;'>{e['author']}</span>
                        </p>
                        <p style='margin:4px 0; color: #1a1a1a;'>
                            📅 <strong style='color: #1a1a1a;'>Date:</strong>
                            <span style='color: #1a1a1a;'>
                            {str(e['date'])[:10]}</span>
                        </p>
                        <hr style='margin: 8px 0; border-color: #e0e0e0;'>
                        <p style='margin:0; color: #333333; font-size: 13px;'>
                            {e['preview']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()

    # Input box
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


# ─── MAIN ────────────────────────────────────────────────────
def main():
    init_audit_table()

    if not st.session_state.logged_in:
        show_login()
    else:
        show_chat()


if __name__ == "__main__":
    main()