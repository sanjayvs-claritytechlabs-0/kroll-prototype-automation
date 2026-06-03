"""Review OCR extraction results before patient search."""

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from apps.pharmacy_simulator.extraction.models import ExtractionResult
from apps.pharmacy_simulator.widgets.accessibility import set_accessible

DISPLAY_FIELDS = (
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("dob", "Date Of Birth"),
    ("phone", "Phone"),
    ("email", "Email"),
    ("health_card", "Health Card"),
)


class ExtractionResultDialog(QDialog):
    """Show extracted fields and raw OCR text for review."""

    def __init__(self, result: ExtractionResult, parent=None) -> None:
        super().__init__(parent)
        self._result = result

        self.setWindowTitle("Extracted Patient Data")
        self.setMinimumWidth(480)
        set_accessible(self, "dlg_extraction_result", "dlg_extraction_result")

        layout = QVBoxLayout(self)

        meta = QLabel(
            f"OCR: {result.ocr_provider}  |  "
            f"Extraction: {result.extraction_provider}  |  "
            f"Confidence: {result.confidence:.0%}"
        )
        meta.setWordWrap(True)
        set_accessible(meta, "lbl_extraction_meta")
        layout.addWidget(meta)

        form = QFormLayout()
        form.setVerticalSpacing(8)
        for key, label in DISPLAY_FIELDS:
            value = result.fields.get(key, "")
            display = str(value) if value else "(not found)"
            field_label = QLabel(display)
            field_label.setWordWrap(True)
            set_accessible(field_label, f"lbl_extracted_{key}")
            form.addRow(f"{label}:", field_label)
        layout.addLayout(form)

        raw_label = QLabel("Raw OCR Text:")
        set_accessible(raw_label, "lbl_raw_ocr")
        layout.addWidget(raw_label)

        raw_text = QPlainTextEdit()
        raw_text.setReadOnly(True)
        raw_text.setPlainText(result.raw_text[:4000])
        raw_text.setMaximumHeight(140)
        set_accessible(raw_text, "txt_raw_ocr")
        layout.addWidget(raw_text)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText("Search Patient")
            set_accessible(ok_btn, "btn_extraction_search")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def result(self) -> ExtractionResult:
        return self._result
