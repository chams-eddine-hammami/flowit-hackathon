# Jira Connector — Project Management Category
# Adapter: Jira
# Alternatives: Asana, Monday, Trello — same interface

import json
import os
from connectors.base_connector import BaseConnector

class JiraConnector(BaseConnector):

    def __init__(self, file_path: str):
        super().__init__(
            source_name="jira_tickets",
            source_type="document"
        )
        self.file_path = file_path

    def connect(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Jira data not found: {self.file_path}")
        self.log(f"Connected to Jira: {self.file_path}")
        return True

    def extract(self):
        with open(self.file_path, "r") as f:
            data = json.load(f)
        self.log(f"Extracted {len(data)} Jira tickets")
        return data

    def validate(self, data):
        required = ["id", "ticket_id", "title", "status", "content"]
        valid = [item for item in data
                 if all(f in item for f in required)]
        self.log(f"Validated: {len(valid)}/{len(data)} tickets")
        return valid

    def send(self, data):
        normalized = []
        for item in data:
            normalized.append({
                "source_id": item["id"],
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": item.get("assignee", ""),
                "author_name": item.get("assignee", "").split("@")[0],
                "timestamp": item["updated_at"],
                "content": item["content"],
                "metadata": {
                    "ticket_id": item["ticket_id"],
                    "project": item["project"],
                    "status": item["status"],
                    "priority": item["priority"]
                }
            })
        self.log(f"Normalized {len(normalized)} Jira tickets")
        return normalized


def run_jira_connector():
    connector = JiraConnector("data/raw/jira_tickets.json")
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)
    print(f"\n=== JIRA CONNECTOR OUTPUT ===")
    for item in normalized:
        print(f"- [{item['metadata']['status']}] {item['metadata']['ticket_id']}: {item['content'][:60]}...")
    return normalized

if __name__ == "__main__":
    run_jira_connector()