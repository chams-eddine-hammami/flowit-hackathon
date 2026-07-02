# Normalization Pipeline
# Runs all connectors and stores everything in the database

import json
import sqlite3
from normalization.database import get_connection, init_database
from connectors.chat_connector import ChatConnector
from connectors.email_connector import EmailConnector
from connectors.document_connector import DocumentConnector
from connectors.survey_connector import SurveyConnector

def store_documents(normalized_data: list):
    """Store normalized data from any connector into database."""
    conn = get_connection()
    cursor = conn.cursor()

    count = 0
    for item in normalized_data:
        # Check if already exists — avoid duplicates
        cursor.execute(
            "SELECT id FROM raw_documents WHERE source_id = ?",
            (item["source_id"],)
        )
        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO raw_documents
                (source_id, source_system, source_type, extracted_at,
                 author_email, author_name, timestamp, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["source_id"],
                item["source_system"],
                item["source_type"],
                item["extracted_at"],
                item["author_email"],
                item["author_name"],
                item["timestamp"],
                item["content"],
                json.dumps(item["metadata"])
            ))
            count += 1

    conn.commit()
    conn.close()
    return count


def run_pipeline():
    """Run all connectors and store everything in database."""

    print("\n🚀 Starting Normalization Pipeline...")
    print("=" * 50)

    # Initialize database
    init_database()

    # --- CONNECTOR 1: Chat ---
    print("\n📱 Running Chat Connector...")
    chat = ChatConnector("data/raw/chat_messages.json")
    chat.connect()
    chat_raw = chat.extract()
    chat_valid = chat.validate(chat_raw)
    chat_normalized = chat.send(chat_valid)
    chat_stored = store_documents(chat_normalized)
    print(f"✅ Chat: {chat_stored} new records stored")

    # --- CONNECTOR 2: Email ---
    print("\n📧 Running Email Connector...")
    email = EmailConnector("data/raw/emails.json")
    email.connect()
    email_raw = email.extract()
    email_valid = email.validate(email_raw)
    email_normalized = email.send(email_valid)
    email_stored = store_documents(email_normalized)
    print(f"✅ Email: {email_stored} new records stored")

    # --- CONNECTOR 3: Documents ---
    print("\n📄 Running Document Connector...")
    doc = DocumentConnector("data/raw/documents.json")
    doc.connect()
    doc_raw = doc.extract()
    doc_valid = doc.validate(doc_raw)
    doc_normalized = doc.send(doc_valid)
    doc_stored = store_documents(doc_normalized)
    print(f"✅ Documents: {doc_stored} new records stored")

    # --- CONNECTOR 4: Survey ---
    print("\n📊 Running Survey Connector...")
    survey = SurveyConnector(
        "data/structured/alpenblick_hospitality_export_enriched.csv"
    )
    survey.connect()
    survey_raw = survey.extract()
    survey_valid = survey.validate(survey_raw)
    survey_normalized = survey.send(survey_valid)
    survey_stored = store_documents(survey_normalized)
    print(f"✅ Survey: {survey_stored} new records stored")

    # --- SUMMARY ---
    print("\n" + "=" * 50)
    print("📊 PIPELINE SUMMARY:")
    total = chat_stored + email_stored + doc_stored + survey_stored
    print(f"  Chat messages : {chat_stored}")
    print(f"  Emails        : {email_stored}")
    print(f"  Documents     : {doc_stored}")
    print(f"  Survey rows   : {survey_stored}")
    print(f"  TOTAL stored  : {total}")
    print("=" * 50)
    print("✅ Pipeline complete!")

    return total


if __name__ == "__main__":
    run_pipeline()