# Base Connector — every connector must follow this interface
# This is what makes the system GENERIC — not one connector per tool

from abc import ABC, abstractmethod
from datetime import datetime
import json

class BaseConnector(ABC):
    """
    Every connector — Teams, Email, Document, Survey —
    must implement these 5 methods.
    Adding a new source = implement these 5 functions only.
    Nothing else in the system changes.
    """

    def __init__(self, source_name: str, source_type: str):
        self.source_name = source_name
        self.source_type = source_type
        self.extracted_at = datetime.utcnow().isoformat()

    @abstractmethod
    def connect(self):
        """Establish connection to the source."""
        pass

    @abstractmethod
    def extract(self):
        """Pull raw data from the source."""
        pass

    @abstractmethod
    def validate(self, data):
        """Check data quality."""
        pass

    @abstractmethod
    def send(self, data):
        """Send normalized data to next layer."""
        pass

    def log(self, message: str):
        """Log what happened — for audit trail."""
        print(f"[{self.source_name}] {self.extracted_at} — {message}")