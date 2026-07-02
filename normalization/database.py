# Database setup — SQLite for fast local demo
# In production this would be PostgreSQL

import sqlite3
import os

DB_PATH = "data/flowit.db"

def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Main table — stores ALL normalized data from ALL sources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT,
            source_system TEXT,
            source_type TEXT,
            extracted_at TEXT,
            author_email TEXT,
            author_name TEXT,
            timestamp TEXT,
            content TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # AI enrichment table — Claude's analysis of each document
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enriched_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_document_id INTEGER,
            people_mentioned TEXT,
            projects_mentioned TEXT,
            sentiment TEXT,
            key_topics TEXT,
            decisions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (raw_document_id) REFERENCES raw_documents(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

if __name__ == "__main__":
    init_database()