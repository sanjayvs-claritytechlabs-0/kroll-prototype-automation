"""Project paths for automation controller."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"
AUTOMATION_LOG = LOG_DIR / "automation.jsonl"
TEST_PATIENT_CONFIG = PROJECT_ROOT / "config" / "automation_test_patient.json"
