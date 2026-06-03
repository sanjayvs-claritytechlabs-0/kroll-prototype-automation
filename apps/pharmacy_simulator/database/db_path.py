"""Database file location relative to project root."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "database" / "pharmacy.db"
INBOX_STORAGE = PROJECT_ROOT / "database" / "inbox"
