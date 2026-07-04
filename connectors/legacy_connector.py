# Legacy System Connector
# Assumption: Company runs an old SQL-based HR and Operations system
# Built 10+ years ago — cannot be modified — read only access
#
# ARCHITECTURE DECISION:
# We never modify the legacy system.
# We only READ from it via a read-only connection.
# The legacy system keeps running normally.
# Our new AI stack grows alongside it.
# This is the "Strangler Fig" pattern.

import sqlite3
import os
from datetime import datetime
from connectors.base_connector import BaseConnector
from normalization.database import get_connection

# ─── CREATE FAKE LEGACY DATABASE ─────────────────────────────
LEGACY_DB_PATH = "data/legacy_system.db"

def create_legacy_system():
    """
    Simulate a legacy SQL database.
    In production this would be Oracle, SAP, or MySQL
    running on company servers.
    We connect read-only — never write.
    """
    conn = sqlite3.connect(LEGACY_DB_PATH)
    cursor = conn.cursor()

    # Legacy employee table — old format, old naming
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EMPLOYEES (
            EMP_ID INTEGER PRIMARY KEY,
            FIRST_NM TEXT,
            LAST_NM TEXT,
            EMAIL_ADDR TEXT,
            DEPT_CD TEXT,
            DEPT_NM TEXT,
            JOB_TITLE TEXT,
            START_DT TEXT,
            STATUS_CD TEXT
        )
    """)

    # Legacy project table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PROJECTS (
            PROJ_ID INTEGER PRIMARY KEY,
            PROJ_NM TEXT,
            DEPT_CD TEXT,
            OWNER_EMP_ID INTEGER,
            START_DT TEXT,
            END_DT TEXT,
            STATUS_CD TEXT,
            BUDGET_AMT REAL
        )
    """)

    # Insert legacy employee data
    employees = [
    (1001, 'Respondent', '668738', 'respondent_668738@alpenblick.com',
     'LUC_OPS', 'Lucerne Operations', 'Project Lead - Guest Experience Initiative', '2019-03-01', 'ACT'),
    (1002, 'Respondent', '668737', 'respondent_668737@alpenblick.com',
     'LUC_OPS', 'Lucerne Operations', 'IT Liaison', '2020-06-15', 'ACT'),
    (1003, 'Respondent', '668736', 'respondent_668736@alpenblick.com',
     'LUC_OPS', 'Lucerne Operations', 'Operations Manager', '2018-01-10', 'ACT'),
    (1004, 'Respondent', '668735', 'respondent_668735@alpenblick.com',
     'HR', 'Human Resources', 'HR Director', '2018-05-01', 'ACT'),
    (1005, 'CFO', 'Alpenblick', 'cfo@alpenblick.com',
     'FIN', 'Finance', 'Chief Financial Officer', '2015-09-01', 'ACT'),
]

    cursor.executemany("""
        INSERT OR REPLACE INTO EMPLOYEES
        (EMP_ID, FIRST_NM, LAST_NM, EMAIL_ADDR,
         DEPT_CD, DEPT_NM, JOB_TITLE, START_DT, STATUS_CD)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)

    # Insert legacy project data
    projects = [
        (2001, 'Lucerne Guest Experience Initiative',
         'LUC_OPS', 1001, '2026-06-01', '2026-07-15', 'AT_RISK', 50000.00),
        (2002, 'Freiburg Panorama Resort Renovation',
         'FRB_OPS', 1003, '2026-05-01', '2026-12-31', 'ON_TRACK', 250000.00),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO PROJECTS
        (PROJ_ID, PROJ_NM, DEPT_CD, OWNER_EMP_ID,
         START_DT, END_DT, STATUS_CD, BUDGET_AMT)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, projects)

    conn.commit()
    conn.close()
    print("✅ Legacy system database created")


# ─── LEGACY CONNECTOR ────────────────────────────────────────
class LegacyConnector(BaseConnector):
    """
    Read-only connector to legacy SQL system.
    Translates old column names to our common model.
    Legacy system never touched — only read.
    """

    def __init__(self):
        super().__init__(
            source_name="legacy_hr_system",
            source_type="document"
        )
        self.db_path = LEGACY_DB_PATH

    def connect(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Legacy system not found: {self.db_path}"
            )
        self.log("Connected to legacy HR system (READ ONLY)")
        return True

    def extract(self):
        """Extract employees and projects from legacy system."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Read employees
        cursor.execute("SELECT * FROM EMPLOYEES")
        employees = [dict(row) for row in cursor.fetchall()]

        # Read projects with owner info
        cursor.execute("""
            SELECT p.*, e.EMAIL_ADDR as OWNER_EMAIL,
                   e.FIRST_NM || ' ' || e.LAST_NM as OWNER_NAME
            FROM PROJECTS p
            LEFT JOIN EMPLOYEES e ON p.OWNER_EMP_ID = e.EMP_ID
        """)
        projects = [dict(row) for row in cursor.fetchall()]

        conn.close()
        self.log(
            f"Extracted {len(employees)} employees "
            f"and {len(projects)} projects from legacy system"
        )
        return {"employees": employees, "projects": projects}

    def validate(self, data):
        """Basic validation of legacy data."""
        employees = data.get("employees", [])
        projects = data.get("projects", [])
        self.log(
            f"Validated: {len(employees)} employees, "
            f"{len(projects)} projects"
        )
        return data

    def send(self, data):
        """
        Normalize legacy data to our common model.
        Old column names (EMP_ID, FIRST_NM) → our format.
        """
        normalized = []

        # Normalize employees
        for emp in data["employees"]:
            normalized.append({
                "source_id": f"legacy_emp_{emp['EMP_ID']}",
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": emp["EMAIL_ADDR"],
                "author_name": f"{emp['FIRST_NM']} {emp['LAST_NM']}",
                "timestamp": emp["START_DT"],
                "content": (
                    f"Employee: {emp['FIRST_NM']} {emp['LAST_NM']}. "
                    f"Role: {emp['JOB_TITLE']}. "
                    f"Department: {emp['DEPT_NM']}. "
                    f"Status: {emp['STATUS_CD']}. "
                    f"Started: {emp['START_DT']}."
                ),
                "metadata": {
                    "type": "employee_record",
                    "department": emp["DEPT_NM"],
                    "job_title": emp["JOB_TITLE"],
                    "status": emp["STATUS_CD"]
                }
            })

        # Normalize projects
        for proj in data["projects"]:
            status_map = {
                "AT_RISK": "At Risk",
                "ON_TRACK": "On Track",
                "COMPLETED": "Completed",
                "ON_HOLD": "On Hold"
            }
            status = status_map.get(proj["STATUS_CD"], proj["STATUS_CD"])

            normalized.append({
                "source_id": f"legacy_proj_{proj['PROJ_ID']}",
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": proj.get("OWNER_EMAIL", ""),
                "author_name": proj.get("OWNER_NAME", ""),
                "timestamp": proj["START_DT"],
                "content": (
                    f"Project: {proj['PROJ_NM']}. "
                    f"Status: {status}. "
                    f"Budget: {proj['BUDGET_AMT']} EUR. "
                    f"Owner: {proj.get('OWNER_NAME', 'Unknown')}. "
                    f"Start: {proj['START_DT']}. "
                    f"End: {proj['END_DT']}."
                ),
                "metadata": {
                    "type": "project_record",
                    "status": status,
                    "budget": proj["BUDGET_AMT"],
                    "department": proj["DEPT_CD"]
                }
            })

        self.log(
            f"Normalized {len(normalized)} records "
            f"from legacy system"
        )
        return normalized


def run_legacy_connector():
    """Create legacy system and run connector."""

    # Create the fake legacy database
    create_legacy_system()

    # Run connector
    connector = LegacyConnector()
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)

    print(f"\n=== LEGACY SYSTEM OUTPUT ===")
    for item in normalized:
        print(f"\n📋 {item['source_id']}")
        print(f"   {item['content'][:100]}...")

    # Store in main database
    from normalization.pipeline import store_documents
    stored = store_documents(normalized)
    print(f"\n✅ {stored} legacy records added to pipeline")

    return normalized


if __name__ == "__main__":
    run_legacy_connector()