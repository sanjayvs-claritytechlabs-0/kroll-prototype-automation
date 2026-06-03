"""OCR and LLM extraction provider interfaces (PRD)."""

from __future__ import annotations

from typing import Protocol

from apps.pharmacy_simulator.extraction.models import OCRResult


class IOCRProvider(Protocol):
    """Extract raw text from a document file."""

    @property
    def name(self) -> str: ...

    def extract_text(self, file_path: str) -> OCRResult: ...


class IExtractionProvider(Protocol):
    """Convert raw OCR text into structured patient data."""

    @property
    def name(self) -> str: ...

    def extract_fields(self, text: str) -> dict[str, str]: ...
