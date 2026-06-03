"""Document viewer — preview incoming documents (OCR in Module 8)."""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.database.inbox_repository import InboxRepository
from apps.pharmacy_simulator.widgets.accessibility import set_accessible


class DocumentViewerWindow(QWidget):
    """Preview a document from the inbox."""

    process_requested = pyqtSignal(int)

    def __init__(
        self,
        document: dict,
        repository: InboxRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._document = document
        self._repository = repository
        doc_id = int(document["id"])
        self.setWindowTitle(f"Document Viewer — {document.get('file_name', 'Document')}")
        self.setMinimumSize(640, 520)
        set_accessible(self, "win_document_viewer", "win_document_viewer")
        self._build_ui()
        self._repository.update_status(doc_id, "Opened")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        meta = QLabel(
            f"Source: {self._document.get('source_type', '')}  |  "
            f"From: {self._document.get('sender', '')}  |  "
            f"Subject: {self._document.get('subject', '')}"
        )
        meta.setWordWrap(True)
        set_accessible(meta, "lbl_document_meta")
        layout.addWidget(meta)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.StyledPanel)
        set_accessible(scroll, "scroll_document_preview")

        preview_host = QWidget()
        preview_layout = QVBoxLayout(preview_host)
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_accessible(self._preview_label, "lbl_document_preview")

        self._text_preview = QTextEdit()
        self._text_preview.setReadOnly(True)
        set_accessible(self._text_preview, "txt_document_preview")

        file_path = str(self._document.get("file_path", ""))
        path = Path(file_path)

        if self._repository.is_image(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    580,
                    720,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._preview_label.setPixmap(scaled)
                preview_layout.addWidget(self._preview_label)
            else:
                self._text_preview.setPlainText(f"Unable to load image: {path.name}")
                preview_layout.addWidget(self._text_preview)
        elif self._repository.is_pdf(file_path):
            self._text_preview.setPlainText(
                f"PDF document: {path.name}\n\n"
                f"Path: {file_path}\n\n"
                "PDF preview and OCR extraction will be available in Module 8."
            )
            preview_layout.addWidget(self._text_preview)
        else:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                content = f"Unable to read file: {exc}"
            self._text_preview.setPlainText(content)
            preview_layout.addWidget(self._text_preview)

        scroll.setWidget(preview_host)
        layout.addWidget(scroll)

        button_row = QHBoxLayout()
        self.btn_process = QPushButton("Process Document")
        set_accessible(self.btn_process, "btn_process_document")
        self.btn_process.clicked.connect(self._on_process)

        self.btn_close = QPushButton("Close")
        set_accessible(self.btn_close, "btn_close_document_viewer")
        self.btn_close.clicked.connect(self.close)

        button_row.addWidget(self.btn_process)
        button_row.addStretch()
        button_row.addWidget(self.btn_close)
        layout.addLayout(button_row)

    def _on_process(self) -> None:
        doc_id = int(self._document["id"])
        self._repository.update_status(doc_id, "Processing")
        self.process_requested.emit(doc_id)
        self.close()

    @property
    def document_id(self) -> int:
        return int(self._document["id"])
