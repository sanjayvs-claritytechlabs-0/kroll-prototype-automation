"""Project paths for workflow engine and audit storage."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"
AUDIT_DB_PATH = PROJECT_ROOT / "database" / "workflow_audit.db"
AUDIT_JSONL = LOG_DIR / "workflow_audit.jsonl"
INBOX_WORKFLOW_CONFIG = PROJECT_ROOT / "config" / "workflow_inbox_to_save.json"
