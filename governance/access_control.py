# Access Control — Governance Layer
# Defines what each role can see and access
# Permissions enforced BEFORE any data is returned to user

# ─── ROLE DEFINITIONS ────────────────────────────────────────
ROLES = {
    "CEO — Full Access": {
        "can_see": ["chat_messaging", "email", "document", "survey"],
        "blocked_topics": [],
        "description": "Full access to all sources and all teams"
    },
    "CFO — Finance & Operations": {
        "can_see": ["email", "document", "survey"],
        "blocked_topics": [],
        "description": "Access to financial documents and surveys"
    },
    "HR Manager — People & Surveys": {
        "can_see": ["survey", "document"],
        "blocked_topics": ["budget", "financial", "finance", "freiburg renovation cost"],
        "description": "Access to people data and survey results only"
    },
    "Operations Manager — Teams & Projects": {
        "can_see": ["chat_messaging", "email", "document"],
        "blocked_topics": ["salary", "payroll", "exit interview", "financial"],
        "description": "Access to operational communications only"
    }
}


def get_allowed_sources(role: str) -> list:
    """Return which source types this role can access."""
    if role not in ROLES:
        return []
    return ROLES[role]["can_see"]


def get_blocked_topics(role: str) -> list:
    """Return topics this role cannot ask about."""
    if role not in ROLES:
        return []
    return ROLES[role].get("blocked_topics", [])


def is_question_allowed(role: str, question: str) -> bool:
    """
    Check if this role is allowed to ask this question.
    Returns False if question touches a blocked topic.
    """
    blocked = get_blocked_topics(role)
    question_lower = question.lower()
    for topic in blocked:
        if topic in question_lower:
            return False
    return True


def can_access(role: str, source_type: str) -> bool:
    """Check if a role can access a specific source type."""
    allowed = get_allowed_sources(role)
    return source_type in allowed


def get_role_description(role: str) -> str:
    """Return human readable description of role permissions."""
    if role not in ROLES:
        return "Unknown role"
    return ROLES[role]["description"]


def filter_results_by_role(results: list, role: str) -> list:
    """
    Filter search results based on role permissions.
    Called BEFORE sending anything to Claude.
    Data never reaches AI if user cannot see it.
    """
    allowed_sources = get_allowed_sources(role)
    filtered = [ 
        doc for doc in results
        if doc['source_type'] in allowed_sources
    ]
    return filtered