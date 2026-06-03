"""Prototype OCR — reads plain text files (simulates OCR output)."""

from __future__ import annotations

from pathlib import Path

from apps.pharmacy_simulator.extraction.models import OCRResult


class TextFileOCRProvider:
    """Use file contents directly as OCR text (prototype / sample forms)."""

    @property
    def name(self) -> str:
        return "TextFileOCRProvider"

    def extract_text(self, file_path: str) -> OCRResult:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="replace")
        return OCRResult(text=text, provider=self.name, source_path=str(path.resolve()))


class StubImageOCRProvider:
    """Placeholder for Tesseract/PaddleOCR — reads sidecar .txt if present."""

    @property
    def name(self) -> str:
        return "StubImageOCRProvider"

    def extract_text(self, file_path: str) -> OCRResult:
        path = Path(file_path)
        sidecar = path.with_suffix(".txt")
        if sidecar.exists():
            text = sidecar.read_text(encoding="utf-8", errors="replace")
        else:
            text = (
                f"[OCR stub — image: {path.name}]\n"
                "Real OCR (Tesseract/PaddleOCR) not configured.\n"
                "Upload a .txt form or add a sidecar .txt with the same name."
            )
        return OCRResult(text=text, provider=self.name, source_path=str(path.resolve()))


class StubPdfOCRProvider:
    """Placeholder for PDF OCR — reads sidecar .txt if present."""

    @property
    def name(self) -> str:
        return "StubPdfOCRProvider"

    def extract_text(self, file_path: str) -> OCRResult:
        path = Path(file_path)
        sidecar = path.with_suffix(".txt")
        if sidecar.exists():
            text = sidecar.read_text(encoding="utf-8", errors="replace")
        else:
            text = (
                f"[OCR stub — PDF: {path.name}]\n"
                "Real PDF OCR not configured.\n"
                "Place a .txt sidecar next to the PDF for prototype extraction."
            )
        return OCRResult(text=text, provider=self.name, source_path=str(path.resolve()))
