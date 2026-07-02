# Entity Resolution
# Finds that the same person appears across different sources
# and merges them into ONE unified profile

import sqlite3
import json
from normalization.database import get_connection, init_database

def init_entity_tables():
    """Create entity and relationship tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Unified person profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            sources TEXT,
            first_seen TEXT,
            last_seen TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Relationships between entities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_email TEXT,
            to_email TEXT,
            relationship_type TEXT,
            evidence TEXT,
            source_system TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Entity tables created")


def resolve_entities():
    """
    Find all unique people across all sources.
    Merge them into unified profiles.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get all unique emails from all sources
    cursor.execute("""
        SELECT DISTINCT author_email, author_name,
               MIN(timestamp) as first_seen,
               MAX(timestamp) as last_seen,
               GROUP_CONCAT(DISTINCT source_system) as sources
        FROM raw_documents
        WHERE author_email IS NOT NULL
        AND author_email != ''
        GROUP BY author_email
    """)

    people = cursor.fetchall()
    print(f"\n👥 Found {len(people)} unique people across all sources")

    # Store unified profiles
    for person in people:
        cursor.execute("""
            INSERT OR REPLACE INTO entities
            (email, name, sources, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
        """, (
            person["author_email"],
            person["author_name"],
            person["sources"],
            person["first_seen"],
            person["last_seen"]
        ))

    conn.commit()

    # Show results
    cursor.execute("SELECT * FROM entities LIMIT 10")
    entities = cursor.fetchall()

    print("\n=== UNIFIED PERSON PROFILES ===")
    for e in entities:
        print(f"\n👤 {e['email']}")
        print(f"   Name    : {e['name']}")
        print(f"   Sources : {e['sources']}")
        print(f"   Active  : {e['first_seen']} → {e['last_seen']}")

    conn.close()
    return len(people)


def resolve_relationships():
    """
    Find relationships between people.
    Who emailed who? Who works in which team?
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Find email relationships — who sent to who
    cursor.execute("""
        SELECT author_email, metadata
        FROM raw_documents
        WHERE source_type = 'email'
    """)

    emails = cursor.fetchall()

    print(f"\n🔗 Building relationships from {len(emails)} emails...")

    for email in emails:
        try:
            metadata = json.loads(email["metadata"])
            to_email = metadata.get("to", "")
            if to_email and email["author_email"]:
                cursor.execute("""
                    INSERT INTO relationships
                    (from_email, to_email, relationship_type,
                     evidence, source_system)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    email["author_email"],
                    to_email,
                    "emailed",
                    f"Sent email to {to_email}",
                    "outlook_email"
                ))
        except:
            pass

    conn.commit()

    # Show relationships
    cursor.execute("SELECT * FROM relationships LIMIT 5")
    rels = cursor.fetchall()

    print("\n=== RELATIONSHIPS FOUND ===")
    for r in rels:
        print(f"  {r['from_email']} → [{r['relationship_type']}] → {r['to_email']}")

    conn.close()


def run_entity_resolution():
    init_entity_tables()
    resolve_entities()
    resolve_relationships()
    print("\n✅ Entity resolution complete!")


if __name__ == "__main__":
    run_entity_resolution()