"""Main application window — Kroll by Telus Health."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.data.sample_patients import SAMPLE_PATIENTS
from apps.pharmacy_simulator.database.inbox_repository import InboxRepository
from apps.pharmacy_simulator.database.patient_repository import PatientRepository
from apps.pharmacy_simulator.dialogs.extraction_result_dialog import ExtractionResultDialog
from apps.pharmacy_simulator.dialogs.open_patient_dialog import OpenPatientDialog
from apps.pharmacy_simulator.extraction.document_processor import DocumentProcessor
from apps.pharmacy_simulator.extraction.models import ExtractionResult
from apps.pharmacy_simulator.extraction.logging import log_extraction
from apps.pharmacy_simulator.widgets.accessibility import set_accessible
from apps.pharmacy_simulator.widgets.message_boxes import show_warning
from apps.pharmacy_simulator.windows.inbox_window import InboxWindow
from apps.pharmacy_simulator.windows.patient_record import PatientRecordWindow
from apps.pharmacy_simulator.windows.patient_search import PatientSearchWindow


class MainWindow(QMainWindow):
    """Primary shell for the pharmacy simulator."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kroll by Telus Health")
        self.setMinimumSize(1024, 768)
        set_accessible(self, "win_main", "win_main")
        self._patient_windows: list[PatientRecordWindow] = []
        self._search_windows: list[PatientSearchWindow] = []
        self._inbox_windows: list[InboxWindow] = []
        self._repository = PatientRepository()
        self._inbox_repository = InboxRepository()
        self._document_processor = DocumentProcessor(self._inbox_repository)
        self._pending_extraction: ExtractionResult | None = None
        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        new_patient_action = QAction("&New Patient Record", self)
        new_patient_action.setShortcut("Ctrl+N")
        new_patient_action.triggered.connect(self.open_new_patient)
        file_menu.addAction(new_patient_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        documents_menu = menu_bar.addMenu("&Documents")
        inbox_action = QAction("&Inbox", self)
        inbox_action.setShortcut("F4")
        inbox_action.triggered.connect(self.open_inbox)
        documents_menu.addAction(inbox_action)

        patient_menu = menu_bar.addMenu("&Patient")
        search_action = QAction("&Search Patient", self)
        search_action.setShortcut("F3")
        search_action.triggered.connect(self.open_patient_search)
        patient_menu.addAction(search_action)

        open_patient_action = QAction("&Open Saved List", self)
        open_patient_action.setShortcut("Ctrl+O")
        open_patient_action.triggered.connect(self.open_existing_patient)
        patient_menu.addAction(open_patient_action)

        test_menu = menu_bar.addMenu("&Test")
        for sample in SAMPLE_PATIENTS:
            action = QAction(f"New with sample — {sample['label']}", self)
            action.triggered.connect(
                lambda checked=False, sid=sample["id"]: self.open_new_patient_with_sample(sid)
            )
            test_menu.addAction(action)

        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        set_accessible(toolbar, "toolbar_main")
        self.addToolBar(toolbar)

        btn_inbox = QPushButton("Inbox")
        set_accessible(btn_inbox, "btn_inbox", "btn_inbox")
        btn_inbox.clicked.connect(self.open_inbox)
        toolbar.addWidget(btn_inbox)

        btn_search = QPushButton("Patient Search")
        set_accessible(btn_search, "btn_patient_search", "btn_patient_search")
        btn_search.clicked.connect(self.open_patient_search)
        toolbar.addWidget(btn_search)

        btn_new = QPushButton("New Patient")
        set_accessible(btn_new, "btn_new_patient", "btn_new_patient")
        btn_new.clicked.connect(self.open_new_patient)
        toolbar.addWidget(btn_new)

    def _build_central(self) -> None:
        central = QWidget()
        set_accessible(central, "central_widget")
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Kroll by Telus Health")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_accessible(title, "lbl_app_title")

        subtitle = QLabel("Pharmacy Automation Prototype")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_accessible(subtitle, "lbl_app_subtitle")

        workflow = QLabel(
            "Workflow: Inbox → OCR/Extract → Patient Search → Patient Record → Save"
        )
        workflow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_accessible(workflow, "lbl_app_workflow")

        hint = QLabel("F4 = Inbox  |  F3 = Patient Search  |  Ctrl+N = new patient")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_accessible(hint, "lbl_app_hint")

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        inbox_btn = QPushButton("Inbox (F4)")
        set_accessible(inbox_btn, "btn_inbox_home", "btn_inbox_home")
        inbox_btn.clicked.connect(self.open_inbox)

        search_btn = QPushButton("Patient Search (F3)")
        set_accessible(search_btn, "btn_patient_search_home", "btn_patient_search_home")
        search_btn.clicked.connect(self.open_patient_search)

        btn_row.addWidget(inbox_btn)
        btn_row.addSpacing(12)
        btn_row.addWidget(search_btn)
        btn_row.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(workflow)
        layout.addSpacing(12)
        layout.addWidget(hint)
        layout.addSpacing(8)
        layout.addLayout(btn_row)

        self.setCentralWidget(central)

    def _build_status_bar(self) -> None:
        status = QStatusBar()
        set_accessible(status, "status_bar_main")
        status.showMessage("Ready — start with Inbox (F4)")
        self.setStatusBar(status)

    def open_inbox(self) -> None:
        window = InboxWindow(self._inbox_repository, parent=None)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        window.document_process_requested.connect(self._on_document_process)
        window.destroyed.connect(
            lambda: self._inbox_windows.remove(window) if window in self._inbox_windows else None
        )
        self._inbox_windows.append(window)
        window.show()
        self.statusBar().showMessage("Inbox open")

    def _on_document_process(self, document_id: int) -> None:
        try:
            result = self._document_processor.process(document_id)
        except (OSError, ValueError) as exc:
            show_warning(self, "Extraction Failed", str(exc))
            return

        dialog = ExtractionResultDialog(result, self)
        if dialog.exec() != ExtractionResultDialog.DialogCode.Accepted:
            return

        self._pending_extraction = result
        self._inbox_repository.update_status(document_id, "Processed")
        log_extraction(result)

        prefill = result.search_prefill()
        if not prefill.get("last_name") and not prefill.get("first_name"):
            show_warning(
                self,
                "Extraction",
                "No patient name found in document.\n"
                "Patient Search will open without prefilled criteria.",
            )
            self.open_patient_search()
            return

        self.open_patient_search(prefill=prefill, auto_search=True)

    def open_patient_search(
        self,
        prefill: dict[str, str] | None = None,
        auto_search: bool = False,
    ) -> None:
        window = PatientSearchWindow(self._repository, parent=None)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        window.patient_selected.connect(self._on_patient_selected_from_search)
        window.create_patient_requested.connect(self.open_new_patient_with_prefill)
        window.destroyed.connect(
            lambda: self._search_windows.remove(window) if window in self._search_windows else None
        )
        self._search_windows.append(window)
        window.show()
        if prefill:
            if auto_search:
                window.prefill_and_search(prefill)
            else:
                window.prefill_criteria(prefill)
        self.statusBar().showMessage("Patient Search open")

    def _on_patient_selected_from_search(self, patient_id: str) -> None:
        self._pending_extraction = None
        self._open_patient_by_id(patient_id)

    def _open_patient_by_id(self, patient_id: str) -> None:
        window = PatientRecordWindow(patient_id=patient_id, parent=None)
        self._show_patient_window(window)

    def open_existing_patient(self) -> None:
        dialog = OpenPatientDialog(self._repository, self)
        if dialog.exec() != OpenPatientDialog.DialogCode.Accepted:
            return
        patient_id = dialog.selected_patient_id
        if not patient_id:
            return
        self._open_patient_by_id(patient_id)

    def open_new_patient(self) -> None:
        window = PatientRecordWindow(parent=None)
        self._show_patient_window(window)

    def open_new_patient_with_sample(self, sample_id: str) -> None:
        window = PatientRecordWindow(sample_id=sample_id, parent=None)
        self._show_patient_window(window)

    def open_new_patient_with_prefill(self, prefill: dict[str, str]) -> None:
        merged = dict(prefill)
        if self._pending_extraction:
            merged = {**self._pending_extraction.patient_prefill(), **merged}
            self._pending_extraction = None
        window = PatientRecordWindow(prefill=merged, parent=None)
        self._show_patient_window(window)

    def _show_patient_window(self, window: PatientRecordWindow) -> None:
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        window.destroyed.connect(
            lambda: self._patient_windows.remove(window) if window in self._patient_windows else None
        )
        self._patient_windows.append(window)
        window.show()
        self.statusBar().showMessage(f"Opened Patient Record — {window.patient_id}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Kroll by Telus Health",
            "Kroll by Telus Health — Pharmacy Automation Prototype\n\n"
            "Workflow: Inbox → OCR/Extract → Patient Search → Patient Record\n\n"
            "Module 8: Text/regex extraction pipeline with OCR provider stubs.\n"
            "Future: Tesseract, PaddleOCR, OpenAI, Gemini providers.",
        )
