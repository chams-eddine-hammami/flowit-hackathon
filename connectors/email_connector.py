# Email Connector — handles Outlook, Gmail, any IMAP
# Category: Email
# Today's adapter: Outlook (fake data)

import json
import os
from connectors.base_connector import BaseConnector

class EmailConnector(BaseConnector):

    def __init__(self, file_path: str):
        super().__init__(
            source_name="outlook_email",
            source_type="email"
        )
        self.file_path = file_path

    def connect(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Email data not found: {self.file_path}")
        self.log(f"Connected to email source: {self.file_path}")
        return True

    def extract(self):
        with open(self.file_path, "r") as f:
            data = json.load(f)
        self.log(f"Extracted {len(data)} emails")
        return data

    def validate(self, data):
        required_fields = ["id", "from", "to", "subject", "timestamp", "body"]
        valid = []
        for item in data:
            if all(field in item for field in required_fields):
                valid.append(item)
            else:
                self.log(f"Skipping invalid email: {item.get('id', 'unknown')}")
        self.log(f"Validated: {len(valid)}/{len(data)} emails passed")
        return valid

    def send(self, data):
        normalized = []
        for item in data:
            normalized.append({
                "source_id": item["id"],
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": item["from"],
                "author_name": item["from"].split("@")[0],
                "timestamp": item["timestamp"],
                "content": item["body"],
                "metadata": {
                    "to": item["to"],
                    "subject": item["subject"]
                }
            })
        self.log(f"Normalized {len(normalized)} emails ready for pipeline")
        return normalized


def run_email_connector():
    connector = EmailConnector("data/raw/emails.json")
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)

    print("\n=== EMAIL CONNECTOR OUTPUT ===")
    for item in normalized:
        print(f"- [{item['timestamp']}] FROM: {item['author_email']} | SUBJECT: {item['metadata']['subject']}")

    return normalized


if __name__ == "__main__":
    run_email_connector()