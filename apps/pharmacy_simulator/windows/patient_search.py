"""Patient Search — find existing patients before create/update."""

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.database.patient_repository import PatientRepository
from apps.pharmacy_simulator.widgets.accessibility import set_accessible

RESULT_COLUMNS = ("Patient ID", "First Name", "Last Name", "DOB", "Phone")


class PatientSearchWindow(QWidget):
    """Search patients by name/DOB — primary workflow entry (existing patient check)."""

    patient_selected = pyqtSignal(str)
    create_patient_requested = pyqtSignal(dict)

    def __init__(self, repository: PatientRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository = repository
        self.setWindowTitle("Patient Search")
        self.setMinimumSize(720, 520)
        set_accessible(self, "win_patient_search", "win_patient_search")
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Search Patient")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        set_accessible(title, "lbl_patient_search_title")
        layout.addWidget(title)

        hint = QLabel("Check for an existing patient before creating a new record.")
        set_accessible(hint, "lbl_patient_search_hint")
        layout.addWidget(hint)

        criteria_group = QGroupBox("Search Criteria")
        set_accessible(criteria_group, "grp_search_criteria")
        form = QFormLayout(criteria_group)
        form.setVerticalSpacing(10)

        self.txt_first_name = QLineEdit()
        self.txt_first_name.setMinimumHeight(28)
        set_accessible(self.txt_first_name, "txt_search_first_name")

        self.txt_last_name = QLineEdit()
        self.txt_last_name.setMinimumHeight(28)
        set_accessible(self.txt_last_name, "txt_search_last_name")

        self.txt_dob = QDateEdit()
        self.txt_dob.setCalendarPopup(True)
        self.txt_dob.setDisplayFormat("yyyy-MM-dd")
        self._dob_empty = QDate(1900, 1, 1)
        self.txt_dob.setMinimumDate(self._dob_empty)
        self.txt_dob.setDate(self._dob_empty)
        self.txt_dob.setSpecialValueText("(any)")
        self.txt_dob.setMinimumHeight(28)
        set_accessible(self.txt_dob, "txt_search_dob")

        form.addRow("First Name:", self.txt_first_name)
        form.addRow("Last Name:", self.txt_last_name)
        form.addRow("Date Of Birth:", self.txt_dob)
        layout.addWidget(criteria_group)

        search_row = QHBoxLayout()
        self.btn_search = QPushButton("Search")
        set_accessible(self.btn_search, "btn_search_patient")
        self.btn_search.clicked.connect(self._run_search)
        self.btn_clear = QPushButton("Clear")
        set_accessible(self.btn_clear, "btn_clear_search")
        self.btn_clear.clicked.connect(self._clear_criteria)
        search_row.addWidget(self.btn_search)
        search_row.addWidget(self.btn_clear)
        search_row.addStretch()
        layout.addLayout(search_row)

        results_group = QGroupBox("Search Results")
        set_accessible(results_group, "grp_search_results")
        results_layout = QVBoxLayout(results_group)

        self.grid_results = QTableWidget(0, len(RESULT_COLUMNS))
        self.grid_results.setHorizontalHeaderLabels(RESULT_COLUMNS)
        self.grid_results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.grid_results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid_results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid_results.setAlternatingRowColors(True)
        self.grid_results.verticalHeader().setVisible(False)
        self.grid_results.horizontalHeader().setStretchLastSection(True)
        self.grid_results.itemDoubleClicked.connect(lambda _item: self._open_selected())
        set_accessible(self.grid_results, "grid_search_results")
        results_layout.addWidget(self.grid_results)

        self.lbl_result_count = QLabel("Enter criteria and click Search.")
        set_accessible(self.lbl_result_count, "lbl_search_result_count")
        results_layout.addWidget(self.lbl_result_count)
        layout.addWidget(results_group)

        action_row = QHBoxLayout()
        self.btn_open = QPushButton("Open Selected")
        set_accessible(self.btn_open, "btn_open_selected_patient")
        self.btn_open.clicked.connect(self._open_selected)

        self.btn_create = QPushButton("Create New Patient")
        set_accessible(self.btn_create, "btn_create_new_patient")
        self.btn_create.clicked.connect(self._create_new)

        action_row.addWidget(self.btn_open)
        action_row.addWidget(self.btn_create)
        action_row.addStretch()
        layout.addLayout(action_row)

        self.txt_last_name.returnPressed.connect(self._run_search)
        self.txt_first_name.returnPressed.connect(self._run_search)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Return"), self, self._run_search)
        QShortcut(QKeySequence("F2"), self, self._open_selected)

    def _dob_criterion(self) -> str:
        if self.txt_dob.date() == self._dob_empty:
            return ""
        return self.txt_dob.date().toString("yyyy-MM-dd")

    def _clear_criteria(self) -> None:
        self.txt_first_name.clear()
        self.txt_last_name.clear()
        self.txt_dob.setDate(self._dob_empty)
        self.grid_results.setRowCount(0)
        self.lbl_result_count.setText("Enter criteria and click Search.")

    def _run_search(self) -> None:
        first_name = self.txt_first_name.text().strip()
        last_name = self.txt_last_name.text().strip()
        dob = self._dob_criterion()

        if not first_name and not last_name and not dob:
            QMessageBox.information(
                self,
                "Patient Search",
                "Enter at least one search field (First Name, Last Name, or DOB).",
            )
            self.txt_last_name.setFocus()
            return

        results = self._repository.search_patients(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
        )
        self._populate_results(results)

    def _populate_results(self, results: list[dict[str, str]]) -> None:
        self.grid_results.setRowCount(0)
        for row_data in results:
            row = self.grid_results.rowCount()
            self.grid_results.insertRow(row)
            values = (
                row_data.get("patient_id", ""),
                row_data.get("first_name", ""),
                row_data.get("last_name", ""),
                row_data.get("dob", ""),
                row_data.get("phone", ""),
            )
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.grid_results.setItem(row, col, item)

        count = len(results)
        self.lbl_result_count.setText(
            f"{count} patient(s) found." if count else "No patients found — use Create New Patient."
        )

    def _selected_patient_id(self) -> str | None:
        row = self.grid_results.currentRow()
        if row < 0:
            return None
        item = self.grid_results.item(row, 0)
        return item.text() if item else None

    def _open_selected(self) -> None:
        patient_id = self._selected_patient_id()
        if not patient_id:
            QMessageBox.information(self, "Patient Search", "Select a patient from the results.")
            return
        self.patient_selected.emit(patient_id)

    def _create_new(self) -> None:
        prefill: dict[str, str] = {}
        if self.txt_first_name.text().strip():
            prefill["first_name"] = self.txt_first_name.text().strip()
        if self.txt_last_name.text().strip():
            prefill["last_name"] = self.txt_last_name.text().strip()
        dob = self._dob_criterion()
        if dob:
            prefill["dob"] = dob
        self.create_patient_requested.emit(prefill)

    def prefill_criteria(self, prefill: dict[str, str]) -> None:
        """Prefill search fields (e.g. from extracted document data)."""
        self.txt_first_name.setText(prefill.get("first_name", ""))
        self.txt_last_name.setText(prefill.get("last_name", ""))
        dob = prefill.get("dob", "")
        if dob:
            parsed = QDate.fromString(dob, "yyyy-MM-dd")
            if parsed.isValid():
                self.txt_dob.setDate(parsed)
        else:
            self.txt_dob.setDate(self._dob_empty)

    def prefill_and_search(self, prefill: dict[str, str]) -> None:
        """Prefill criteria and run search automatically."""
        self.prefill_criteria(prefill)
        self._run_search()
