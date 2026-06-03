"""OCR and extraction data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRResult:
    """Raw text output from an OCR provider."""

    text: str
    provider: str
    source_path: str


@dataclass
class ExtractionResult:
    """Structured patient fields extracted from document text."""

    document_id: int
    raw_text: str
    fields: dict[str, str] = field(default_factory=dict)
    ocr_provider: str = ""
    extraction_provider: str = ""
    confidence: float = 0.0

    def search_prefill(self) -> dict[str, str]:
        """Fields used to prefill Patient Search."""
        keys = ("first_name", "last_name", "dob")
        return {k: self.fields[k] for k in keys if self.fields.get(k)}

    def patient_prefill(self) -> dict[str, str]:
        """Fields used to prefill a new Patient Record."""
        return dict(self.fields)
