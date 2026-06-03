"""Searchable allergy catalog for the add-allergy flow."""

from __future__ import annotations

import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parents[3] / "config" / "allergy_catalog.json"


def load_allergy_catalog() -> list[str]:
    with _CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def search_allergies(query: str, catalog: list[str] | None = None) -> list[str]:
    items = catalog if catalog is not None else load_allergy_catalog()
    q = query.strip().lower()
    if not q:
        return items
    return [name for name in items if q in name.lower()]
