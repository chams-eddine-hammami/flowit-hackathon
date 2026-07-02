# Document Connector — handles Word, Google Docs, Notion, Confluence
# Category: Documents
# Today's adapter: Local documents (fake data)

import json
import os
from connectors.base_connector import BaseConnector

class DocumentConnector(BaseConnector):

    def __init__(self, file_path: str):
        super().__init__(
            source_name="word_documents",
            source_type="document"
        )
        self.file_path = file_path

    def connect(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Document data not found: {self.file_path}")
        self.log(f"Connected to document source: {self.file_path}")
        return True

    def extract(self):
        with open(self.file_path, "r") as f:
            data = json.load(f)
        self.log(f"Extracted {len(data)} documents")
        return data

    def validate(self, data):
        required_fields = ["id", "title", "author", "created_at", "content"]
        valid = []
        for item in data:
            if all(field in item for field in required_fields):
                valid.append(item)
            else:
                self.log(f"Skipping invalid document: {item.get('id', 'unknown')}")
        self.log(f"Validated: {len(valid)}/{len(data)} documents passed")
        return valid

    def send(self, data):
        normalized = []
        for item in data:
            normalized.append({
                "source_id": item["id"],
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": item["author"],
                "author_name": item["author"].split("@")[0],
                "timestamp": item["created_at"],
                "content": item["content"],
                "metadata": {
                    "title": item["title"]
                }
            })
        self.log(f"Normalized {len(normalized)} documents ready for pipeline")
        return normalized


def run_document_connector():
    connector = DocumentConnector("data/raw/documents.json")
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)

    print("\n=== DOCUMENT CONNECTOR OUTPUT ===")
    for item in normalized:
        print(f"- [{item['timestamp']}] {item['author_email']} | TITLE: {item['metadata']['title']}")

    return normalized


if __name__ == "__main__":
    run_document_connector()