"""Document OCR + extraction pipeline."""

from __future__ import annotations

from pathlib import Path

from apps.pharmacy_simulator.database.inbox_repository import InboxRepository
from apps.pharmacy_simulator.extraction.interfaces import IExtractionProvider, IOCRProvider
from apps.pharmacy_simulator.extraction.models import ExtractionResult, OCRResult
from apps.pharmacy_simulator.extraction.providers.ocr_providers import (
    StubImageOCRProvider,
    StubPdfOCRProvider,
    TextFileOCRProvider,
)
from apps.pharmacy_simulator.extraction.providers.regex_extraction import RegexExtractionProvider

_TEXT_EXTENSIONS = {".txt", ".text"}


class DocumentProcessor:
    """Run OCR then structured extraction on an inbox document."""

    def __init__(
        self,
        inbox: InboxRepository,
        ocr: IOCRProvider | None = None,
        extractor: IExtractionProvider | None = None,
    ) -> None:
        self._inbox = inbox
        self._ocr = ocr or TextFileOCRProvider()
        self._extractor = extractor or RegexExtractionProvider()

    def _ocr_for_path(self, file_path: str) -> IOCRProvider:
        ext = Path(file_path).suffix.lower()
        if ext in _TEXT_EXTENSIONS:
            return TextFileOCRProvider()
        if self._inbox.is_pdf(file_path):
            return StubPdfOCRProvider()
        if self._inbox.is_image(file_path):
            return StubImageOCRProvider()
        return self._ocr

    def process(self, document_id: int) -> ExtractionResult:
        doc = self._inbox.get_document(document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")

        file_path = str(doc["file_path"])
        ocr_provider = self._ocr_for_path(file_path)
        ocr_result: OCRResult = ocr_provider.extract_text(file_path)

        fields = self._extractor.extract_fields(ocr_result.text)
        confidence = 0.0
        if isinstance(self._extractor, RegexExtractionProvider):
            confidence = self._extractor.confidence(fields)

        return ExtractionResult(
            document_id=document_id,
            raw_text=ocr_result.text,
            fields=fields,
            ocr_provider=ocr_result.provider,
            extraction_provider=self._extractor.name,
            confidence=confidence,
        )
