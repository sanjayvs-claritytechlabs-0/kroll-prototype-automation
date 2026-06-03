"""Future OCR/LLM providers — interfaces only per PRD."""

from __future__ import annotations


class TesseractProvider:
    """Future: pytesseract integration."""

    @property
    def name(self) -> str:
        return "TesseractProvider"

    def extract_text(self, file_path: str):
        raise NotImplementedError("TesseractProvider is not implemented yet.")


class PaddleOCRProvider:
    """Future: PaddleOCR integration."""

    @property
    def name(self) -> str:
        return "PaddleOCRProvider"

    def extract_text(self, file_path: str):
        raise NotImplementedError("PaddleOCRProvider is not implemented yet.")


class OpenAIExtractionProvider:
    """Future: OpenAI structured extraction."""

    @property
    def name(self) -> str:
        return "OpenAIExtractionProvider"

    def extract_fields(self, text: str) -> dict[str, str]:
        raise NotImplementedError("OpenAIExtractionProvider is not implemented yet.")


class GeminiExtractionProvider:
    """Future: Gemini structured extraction."""

    @property
    def name(self) -> str:
        return "GeminiExtractionProvider"

    def extract_fields(self, text: str) -> dict[str, str]:
        raise NotImplementedError("GeminiExtractionProvider is not implemented yet.")
