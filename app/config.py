"""Central configuration. Values can be overridden with environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "sample_tickets.csv"
MODEL_PATH = BASE_DIR / "models" / "ticket_classifier.joblib"


def db_path() -> str:
    # Read at call time so tests can point to a temporary database.
    return os.getenv("TICKET_DB", str(BASE_DIR / "tickets.db"))


# Which team handles which category (simple routing rules).
ASSIGNMENT_RULES = {
    "Network": "network-team",
    "Access": "iam-team",
    "Hardware": "desktop-support",
    "Software": "app-support",
    "Email": "messaging-team",
    "Security": "security-team",
}

# Below this confidence the ticket is flagged for manual triage.
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
