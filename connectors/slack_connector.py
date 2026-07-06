# Slack Connector — Chat & Messaging Category
# Adapter: Slack
# Same category as Teams — swap adapter only
# Proves: adding new tool = new adapter, not new system

import json
import os
from connectors.base_connector import BaseConnector

class SlackConnector(BaseConnector):

    def __init__(self, file_path: str):
        super().__init__(
            source_name="slack_chat",
            source_type="chat_messaging"
        )
        self.file_path = file_path

    def connect(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Slack data not found: {self.file_path}")
        self.log(f"Connected to Slack source: {self.file_path}")
        return True

    def extract(self):
        with open(self.file_path, "r") as f:
            data = json.load(f)
        self.log(f"Extracted {len(data)} Slack messages")
        return data

    def validate(self, data):
        required = ["id", "sender_email", "timestamp", "content"]
        valid = [item for item in data
                 if all(f in item for f in required)]
        self.log(f"Validated: {len(valid)}/{len(data)} messages")
        return valid

    def send(self, data):
        normalized = []
        for item in data:
            normalized.append({
                "source_id": item["id"],
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": item["sender_email"],
                "author_name": item.get("sender", ""),
                "timestamp": item["timestamp"],
                "content": item["content"],
                "metadata": {
                    "platform": "slack",
                    "channel": item.get("channel", "")
                }
            })
        self.log(f"Normalized {len(normalized)} Slack messages")
        return normalized


def run_slack_connector():
    connector = SlackConnector("data/raw/slack_messages.json")
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)
    print(f"\n=== SLACK CONNECTOR OUTPUT ===")
    for item in normalized:
        print(f"- [{item['timestamp']}] {item['author_email']}: {item['content'][:60]}...")
    return normalized

if __name__ == "__main__":
    run_slack_connector()