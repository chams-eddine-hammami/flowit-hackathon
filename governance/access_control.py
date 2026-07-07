# Access Control — Governance Layer
# Defines what each role can see and access
# Permissions enforced BEFORE any data is returned to user

# ─── ROLE DEFINITIONS ────────────────────────────────────────
ROLES = {
    "CEO — Full Access": {
        "can_see": ["chat_messaging", "email", "document", "survey"],
        "blocked_topics": [],
        "description": "Full access — all sources all teams"
    },
    "CFO — Finance & Operations": {
        "can_see": ["email", "document", "survey"],
        "blocked_topics": [
            "exit interview", "personal feedback",
            "resignation reason", "why leaving"
        ],
        "description": "Finance and operations only"
    },
    "HR Manager — People & Surveys": {
        "can_see": ["survey", "document"],
        "blocked_topics": [
            "budget", "financial", "renovation cost",
            "freiburg budget", "approved amount",
            "eur", "cfo approved", "250000", "50000"
        ],
        "description": "People data and surveys only"
    },
    "Operations Manager — Teams & Projects": {
        "can_see": ["chat_messaging", "email", "document"],
        "blocked_topics": [
            "salary", "payroll", "financial",
            "budget", "approved amount", "eur",
            "cost", "renovation budget", "250000", "50000",
            "exit interview", "resignation", "why did",
            "why employees", "resign", "termination"
        ],
        "description": "Operational communications only"
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
    blocked = get_blocked_topics(role)
    question_lower = question.lower()

    # Direct keyword match
    for topic in blocked:
        if topic in question_lower:
            return False

    # Smart semantic blocking for Operations Manager
    if role == "Operations Manager — Teams & Projects":
        financial_signals = [
            'budget', 'cost', 'price', 'eur', 'money',
            'approved amount', 'financial', 'salary',
            'pay', 'compensation', 'wages'
        ]
        resignation_signals = [
            'resign', 'leaving', 'left', 'quit',
            'termination', 'departure', 'exit',
            'why did', 'why employees', 'reason for leaving'
        ]
        for signal in financial_signals + resignation_signals:
            if signal in question_lower:
                return False

    # Smart semantic blocking for HR Manager
    if role == "HR Manager — People & Surveys":
        financial_signals = [
            'budget', 'cost', 'eur', 'money',
            'approved', 'financial', 'renovation cost',
            'how much', 'price', 'amount'
        ]
        for signal in financial_signals:
            if signal in question_lower:
                return False

    # Smart semantic blocking for CFO
    if role == "CFO — Finance & Operations":
        personal_signals = [
            'exit interview', 'resignation letter',
            'why did employees', 'why are employees leaving',
            'personal feedback', 'individual complaint',
            'who resigned', 'who left', 'which employee',
            'personal opinion', 'private feedback'
        ]
        for signal in personal_signals:
            if signal in question_lower:
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