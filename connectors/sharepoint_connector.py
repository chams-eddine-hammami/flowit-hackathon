# SharePoint Connector — File Storage Category
# Adapter: SharePoint
# Same category as Word Documents — swap adapter only

import json
import os
from connectors.base_connector import BaseConnector

class SharePointConnector(BaseConnector):

    def __init__(self, file_path: str):
        super().__init__(
            source_name="sharepoint_files",
            source_type="document"
        )
        self.file_path = file_path

    def connect(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"SharePoint data not found: {self.file_path}")
        self.log(f"Connected to SharePoint: {self.file_path}")
        return True

    def extract(self):
        with open(self.file_path, "r") as f:
            data = json.load(f)
        self.log(f"Extracted {len(data)} SharePoint files")
        return data

    def validate(self, data):
        required = ["id", "title", "author", "created_at", "content"]
        valid = [item for item in data
                 if all(f in item for f in required)]
        self.log(f"Validated: {len(valid)}/{len(data)} files")
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
                    "title": item["title"],
                    "site": item.get("site", "")
                }
            })
        self.log(f"Normalized {len(normalized)} SharePoint files")
        return normalized


def run_sharepoint_connector():
    connector = SharePointConnector("data/raw/sharepoint_files.json")
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)
    print(f"\n=== SHAREPOINT CONNECTOR OUTPUT ===")
    for item in normalized:
        print(f"- {item['author_email']} | {item['metadata']['title']}")
    return normalized

if __name__ == "__main__":
    run_sharepoint_connector()