"""Regex-based field extraction from labeled form text (prototype)."""

from __future__ import annotations

import re

from apps.pharmacy_simulator.extraction.interfaces import IExtractionProvider

_FIELD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("first_name", re.compile(r"^First Name:\s*(.+)$", re.I | re.M)),
    ("last_name", re.compile(r"^Last Name:\s*(.+)$", re.I | re.M)),
    ("middle_name", re.compile(r"^Middle Name:\s*(.+)$", re.I | re.M)),
    ("dob", re.compile(r"^(?:Date of Birth|DOB):\s*(\d{4}-\d{2}-\d{2})$", re.I | re.M)),
    ("phone", re.compile(r"^Phone:\s*([\d\-\(\)\s]+)$", re.I | re.M)),
    ("email", re.compile(r"^Email:\s*(\S+@\S+)$", re.I | re.M)),
    ("health_card", re.compile(r"^Health Card:\s*(\S+)$", re.I | re.M)),
    ("address_line1", re.compile(r"^Address(?: Line 1)?:\s*(.+)$", re.I | re.M)),
    ("city", re.compile(r"^City:\s*(.+?)(?:\s+Province:|\s*$)", re.I | re.M)),
    ("province", re.compile(r"Province:\s*([A-Z]{2})", re.I | re.M)),
    ("postal_code", re.compile(r"Postal(?: Code)?:\s*([A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d)", re.I | re.M)),
    ("gender", re.compile(r"^Gender:\s*(.+)$", re.I | re.M)),
]

_NAME_PATTERN = re.compile(r"^Name:\s*(\S+)\s+(.+)$", re.I | re.M)


def _normalize_phone(raw: str) -> str:
    return re.sub(r"\D", "", raw)


class RegexExtractionProvider:
    """Parse labeled registration forms without an LLM (fast prototype)."""

    @property
    def name(self) -> str:
        return "RegexExtractionProvider"

    def extract_fields(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}

        for key, pattern in _FIELD_PATTERNS:
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if key == "phone":
                    value = _normalize_phone(value)
                fields[key] = value

        if "first_name" not in fields or "last_name" not in fields:
            name_match = _NAME_PATTERN.search(text)
            if name_match:
                fields.setdefault("first_name", name_match.group(1).strip())
                fields.setdefault("last_name", name_match.group(2).strip())

        return fields

    def confidence(self, fields: dict[str, str]) -> float:
        """Simple score based on required search fields present."""
        required = ("last_name", "dob")
        optional = ("first_name", "phone", "email", "health_card")
        score = sum(1 for k in required if fields.get(k)) / len(required) * 0.6
        score += sum(1 for k in optional if fields.get(k)) / len(optional) * 0.4
        return round(min(score, 1.0), 2)
