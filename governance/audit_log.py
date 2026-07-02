# Audit Log — tracks every access
# Who asked what — when — from which role
# Required for compliance and governance

import sqlite3
from datetime import datetime
from normalization.database import get_connection


def init_audit_table():
    """Create audit log table."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_name TEXT,
            user_role TEXT,
            question TEXT,
            sources_accessed TEXT,
            confidence TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def log_access(
    user_name: str,
    user_role: str,
    question: str,
    sources_accessed: list,
    confidence: str
):
    """Log every query — who asked what and when."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_log
        (timestamp, user_name, user_role, question,
         sources_accessed, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        user_name,
        user_role,
        question,
        ", ".join(sources_accessed),
        confidence
    ))

    conn.commit()
    conn.close()


def get_audit_log(limit: int = 20) -> list:
    """Return recent audit log entries."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM audit_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)) 

    results = cursor.fetchall()
    conn.close()
    return results