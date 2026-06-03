"""Prefilled sample patients for prototype testing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "sample_patients.json"


def _load_samples() -> list[dict[str, Any]]:
    with _CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


SAMPLE_PATIENTS: list[dict[str, Any]] = _load_samples()
SAMPLE_BY_ID: dict[str, dict[str, Any]] = {item["id"]: item for item in SAMPLE_PATIENTS}


def get_sample(sample_id: str) -> dict[str, Any] | None:
    return SAMPLE_BY_ID.get(sample_id)
