"""Inbox — incoming fax/email/upload documents."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.database.inbox_repository import InboxRepository
from apps.pharmacy_simulator.widgets.accessibility import set_accessible
from apps.pharmacy_simulator.widgets.message_boxes import ask_yes_no, show_info, show_warning
from apps.pharmacy_simulator.windows.document_viewer import DocumentViewerWindow

COLUMNS = ("Received", "Source", "From", "Subject", "File", "Status")
SOURCE_FILTERS = ["All", "Email", "Fax", "Upload"]


class InboxWindow(QWidget):
    """Simulates fax/email inbox with document upload."""

    document_process_requested = pyqtSignal(int)

    def __init__(self, repository: InboxRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._viewer_windows: list[DocumentViewerWindow] = []

        self.setWindowTitle("Inbox — Incoming Documents")
        self.setMinimumSize(860, 520)
        set_accessible(self, "win_inbox", "win_inbox")
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Incoming Documents")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        set_accessible(title, "lbl_inbox_title")
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_label = QLabel("Show:")
        set_accessible(filter_label, "lbl_inbox_filter")
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(SOURCE_FILTERS)
        self.cmb_filter.setMinimumHeight(28)
        set_accessible(self.cmb_filter, "cmb_inbox_filter")
        self.cmb_filter.currentTextChanged.connect(lambda _text: self.refresh())
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.cmb_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.grid = QTableWidget(0, len(COLUMNS))
        self.grid.setHorizontalHeaderLabels(COLUMNS)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.setAlternatingRowColors(True)
        self.grid.verticalHeader().setVisible(False)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.itemDoubleClicked.connect(lambda _item: self._open_selected())
        set_accessible(self.grid, "grid_inbox", "grid_inbox")
        layout.addWidget(self.grid)

        button_row = QHBoxLayout()

        self.btn_upload_pdf = QPushButton("Upload PDF")
        set_accessible(self.btn_upload_pdf, "btn_upload_pdf")
        self.btn_upload_pdf.clicked.connect(
            lambda: self._upload_file("PDF Files (*.pdf);;All Files (*.*)")
        )

        self.btn_upload_image = QPushButton("Upload Image")
        set_accessible(self.btn_upload_image, "btn_upload_image")
        self.btn_upload_image.clicked.connect(
            lambda: self._upload_file(
                "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*.*)"
            )
        )

        self.btn_open = QPushButton("Open")
        set_accessible(self.btn_open, "btn_inbox_open")
        self.btn_open.clicked.connect(self._open_selected)

        self.btn_delete = QPushButton("Delete")
        set_accessible(self.btn_delete, "btn_inbox_delete")
        self.btn_delete.clicked.connect(self._delete_selected)

        self.btn_refresh = QPushButton("Refresh")
        set_accessible(self.btn_refresh, "btn_inbox_refresh")
        self.btn_refresh.clicked.connect(self.refresh)

        button_row.addWidget(self.btn_upload_pdf)
        button_row.addWidget(self.btn_upload_image)
        button_row.addWidget(self.btn_open)
        button_row.addWidget(self.btn_delete)
        button_row.addWidget(self.btn_refresh)
        button_row.addStretch()
        layout.addLayout(button_row)

    def refresh(self) -> None:
        source = self.cmb_filter.currentText()
        filter_type = "" if source == "All" else source
        documents = self._repository.list_documents(filter_type)

        self.grid.setRowCount(0)
        for doc in documents:
            row = self.grid.rowCount()
            self.grid.insertRow(row)
            received = str(doc.get("received_at", ""))[:19].replace("T", " ")
            values = (
                received,
                doc.get("source_type", ""),
                doc.get("sender", ""),
                doc.get("subject", ""),
                doc.get("file_name", ""),
                doc.get("status", ""),
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, doc["id"])
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.grid.setItem(row, col, item)

    def _selected_document_id(self) -> int | None:
        row = self.grid.currentRow()
        if row < 0:
            return None
        item = self.grid.item(row, 0)
        if item is None:
            return None
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        return int(doc_id) if doc_id is not None else None

    def _upload_file(self, file_filter: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Document", "", file_filter)
        if not path:
            return
        try:
            self._repository.import_upload(path)
        except OSError as exc:
            show_warning(self, "Upload Failed", str(exc))
            return
        self.refresh()
        show_info(self, "Upload", "Document added to inbox.")

    def _open_selected(self) -> None:
        doc_id = self._selected_document_id()
        if doc_id is None:
            show_info(self, "Inbox", "Select a document to open.")
            return
        doc = self._repository.get_document(doc_id)
        if doc is None:
            show_warning(self, "Inbox", "Document not found.")
            return

        viewer = DocumentViewerWindow(doc, self._repository, parent=None)
        viewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        viewer.process_requested.connect(self.document_process_requested.emit)
        viewer.destroyed.connect(
            lambda: self._viewer_windows.remove(viewer) if viewer in self._viewer_windows else None
        )
        self._viewer_windows.append(viewer)
        viewer.show()
        self.refresh()

    def _delete_selected(self) -> None:
        doc_id = self._selected_document_id()
        if doc_id is None:
            return
        doc = self._repository.get_document(doc_id)
        if doc is None:
            return
        name = str(doc.get("file_name", ""))
        if not ask_yes_no(self, "Delete Document", f"Remove '{name}' from inbox?"):
            return
        self._repository.delete_document(doc_id)
        self.refresh()
