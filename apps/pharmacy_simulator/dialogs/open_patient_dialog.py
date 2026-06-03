"""Dialog to open an existing patient from the database."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from apps.pharmacy_simulator.database.patient_repository import PatientRepository
from apps.pharmacy_simulator.widgets.accessibility import set_accessible


class OpenPatientDialog(QDialog):
    """Search and select a saved patient record."""

    def __init__(self, repository: PatientRepository, parent=None) -> None:
        super().__init__(parent)
        self._repository = repository
        self._selected_patient_id: str | None = None

        self.setWindowTitle("Open Patient Record")
        self.setMinimumSize(520, 400)
        set_accessible(self, "dlg_open_patient", "dlg_open_patient")

        layout = QVBoxLayout(self)

        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        set_accessible(search_label, "lbl_open_patient_search")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Patient ID or name...")
        self.txt_search.setMinimumHeight(28)
        set_accessible(self.txt_search, "txt_open_patient_search")
        self.txt_search.textChanged.connect(self._refresh_list)
        search_row.addWidget(search_label)
        search_row.addWidget(self.txt_search)
        layout.addLayout(search_row)

        self.list_patients = QListWidget()
        set_accessible(self.list_patients, "list_open_patients")
        self.list_patients.itemDoubleClicked.connect(self._accept_selection)
        layout.addWidget(self.list_patients)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel
        )
        open_btn = buttons.button(QDialogButtonBox.StandardButton.Open)
        if open_btn:
            set_accessible(open_btn, "btn_open_patient_confirm")
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._all_patients = self._repository.list_patients()
        self._refresh_list()

    def _refresh_list(self) -> None:
        query = self.txt_search.text().strip().lower()
        self.list_patients.clear()
        for patient in self._all_patients:
            label = (
                f"{patient['patient_id']} — "
                f"{patient.get('last_name', '')}, {patient.get('first_name', '')}"
            ).strip(" ,")
            haystack = label.lower()
            if query and query not in haystack:
                continue
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, patient["patient_id"])
            self.list_patients.addItem(item)

    def _accept_selection(self) -> None:
        item = self.list_patients.currentItem()
        if item is None:
            return
        self._selected_patient_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @property
    def selected_patient_id(self) -> str | None:
        return self._selected_patient_id
