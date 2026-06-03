"""Append structured extraction logs (JSON lines)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from apps.pharmacy_simulator.database.db_path import PROJECT_ROOT
from apps.pharmacy_simulator.extraction.models import ExtractionResult

_LOG_PATH = PROJECT_ROOT / "logs" / "extractions.jsonl"


def log_extraction(result: ExtractionResult) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "document_id": result.document_id,
        "ocr_provider": result.ocr_provider,
        "extraction_provider": result.extraction_provider,
        "confidence": result.confidence,
        "fields": result.fields,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
