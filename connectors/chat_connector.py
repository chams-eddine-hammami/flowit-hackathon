# Chat Connector — handles Teams, Slack, Discord, Google Chat
# Category: Chat & Messaging
# Today's adapter: Microsoft Teams (fake data)

import json
import os
from connectors.base_connector import BaseConnector

class ChatConnector(BaseConnector):
    """
    Connects to any chat/messaging platform.
    Current adapter: Teams (via local JSON file for demo)
    To switch to Slack: change connect() and extract() only.
    Everything else stays the same.
    """

    def __init__(self, file_path: str):
        super().__init__(
            source_name="teams_chat",
            source_type="chat_messaging"
        )
        self.file_path = file_path

    def connect(self):
        """Check the source exists and is readable."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Chat data not found: {self.file_path}")
        self.log(f"Connected to chat source: {self.file_path}")
        return True

    def extract(self):
        """Pull raw messages from source."""
        with open(self.file_path, "r") as f:
            data = json.load(f)
        self.log(f"Extracted {len(data)} messages")
        return data

    def validate(self, data):
        """Check every message has required fields."""
        required_fields = ["id", "sender_email", "timestamp", "content"]
        valid = []
        for item in data:
            if all(field in item for field in required_fields):
                valid.append(item)
            else:
                self.log(f"Skipping invalid message: {item.get('id', 'unknown')}")
        self.log(f"Validated: {len(valid)}/{len(data)} messages passed")
        return valid

    def send(self, data):
        """
        Normalize to common format and send to normalization layer.
        Every connector outputs the SAME structure.
        """
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
                    "platform": item.get("platform", "teams"),
                    "channel": item.get("channel", "")
                }
            })
        self.log(f"Normalized {len(normalized)} messages ready for pipeline")
        return normalized


def run_chat_connector():
    """Test the chat connector end to end."""
    connector = ChatConnector("data/raw/chat_messages.json")
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)

    print("\n=== CHAT CONNECTOR OUTPUT ===")
    for item in normalized:
        print(f"- [{item['timestamp']}] {item['author_email']}: {item['content'][:60]}...")

    return normalized


if __name__ == "__main__":
    run_chat_connector()