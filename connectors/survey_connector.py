# Survey Connector — handles Typeform, Google Forms, SurveyMonkey
# Category: Survey & Feedback
# Today's adapter: Alpenblick real CSV dataset from Flowit

import pandas as pd
import os
from connectors.base_connector import BaseConnector

class SurveyConnector(BaseConnector):

    def __init__(self, file_path: str):
        super().__init__(
            source_name="survey_platform",
            source_type="survey"
        )
        self.file_path = file_path

    def connect(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Survey data not found: {self.file_path}")
        self.log(f"Connected to survey source: {self.file_path}")
        return True

    def extract(self):
        df = pd.read_csv(self.file_path)
        self.log(f"Extracted {len(df)} survey responses")
        return df

    def validate(self, data):
        required_columns = ["respondent_id", "answer", "question_text"]
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            self.log(f"Missing columns: {missing}")
            return data
        clean = data.dropna(subset=["respondent_id", "answer"])
        self.log(f"Validated: {len(clean)}/{len(data)} responses passed")
        return clean

    def send(self, data):
        normalized = []
        for _, row in data.iterrows():
            normalized.append({
                "source_id": f"survey_{row['answer_id']}",
                "source_system": self.source_name,
                "source_type": self.source_type,
                "extracted_at": self.extracted_at,
                "author_email": f"respondent_{row['respondent_id']}@alpenblick.com",
                "author_name": f"respondent_{row['respondent_id']}",
                "timestamp": str(row.get("answer_submission_start", "")),
                "content": (
    f"Question:\n{row['question_text']}\n\n"
    f"Score:\n{row['answer']} / 7"
    if row.get("question_type") == "range_slider"
    else (
        f"Question:\n{row['question_text']}\n\n"
        f"Answer:\n{str(row['answer']).replace(' | ', chr(10) + '• ')}"
    )
),
                "metadata": {
    "questionnaire": row.get("questionnaire_title", ""),
    "question_type": row.get("question_type", ""),
    "sentiment": row.get("sentiment", ""),
    "teams": row.get("teams", ""),
    "gender": row.get("gender", ""),
    "topics": row.get("topics", ""),
    "keywords": row.get("keywords", "")
}
            })
        self.log(f"Normalized {len(normalized)} survey responses ready for pipeline")
        return normalized


def run_survey_connector():
    connector = SurveyConnector(
        "data/structured/alpenblick_hospitality_export_enriched.csv"
    )
    connector.connect()
    raw = connector.extract()
    valid = connector.validate(raw)
    normalized = connector.send(valid)

    print("\n=== SURVEY CONNECTOR OUTPUT (first 3) ===")
    for item in normalized[:3]:
        print(f"- {item['author_email']}")
        print(f"  {item['content'][:80]}...")
        print(f"  sentiment: {item['metadata']['sentiment']}")
        print()

    return normalized


if __name__ == "__main__":
    run_survey_connector()