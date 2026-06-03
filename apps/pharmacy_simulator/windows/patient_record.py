"""Patient Record window with tabbed interface and keyboard navigation."""

import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.data.sample_patients import SAMPLE_PATIENTS, get_sample
from apps.pharmacy_simulator.database.patient_repository import PatientRepository
from apps.pharmacy_simulator.tabs.allergies_tab import AllergiesTab
from apps.pharmacy_simulator.tabs.communications_tab import CommunicationsTab
from apps.pharmacy_simulator.tabs.family_tab import FamilyTab
from apps.pharmacy_simulator.tabs.general_tab import GeneralTab
from apps.pharmacy_simulator.tabs.insurance_tab import InsuranceTab
from apps.pharmacy_simulator.validation.patient_validator import validate_patient
from apps.pharmacy_simulator.widgets.accessibility import set_accessible
from apps.pharmacy_simulator.widgets.message_boxes import show_info, show_warning

TAB_DEFINITIONS: list[tuple[str, str, str]] = [
    ("General", "tab_general", "G"),
    ("Insurance", "tab_insurance", "I"),
    ("Family", "tab_family", "F"),
    ("Allergies", "tab_allergies", "A"),
    ("Communications", "tab_communications", "C"),
]

class PatientRecordWindow(QWidget):
    """Modal-style patient record with tabbed interface and keyboard shortcuts."""

    _repository = PatientRepository()

    def __init__(
        self,
        patient_id: str | None = None,
        sample_id: str | None = None,
        prefill: dict[str, str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._patient_id = patient_id or self._generate_patient_id()
        self._is_existing = self._repository.patient_exists(self._patient_id)
        self._pending_sample_id = sample_id
        self._pending_prefill = prefill
        self.setWindowTitle(f"Patient Record — {self._patient_id}")
        self.setMinimumSize(900, 650)
        set_accessible(self, "win_patient_record", "win_patient_record")
        self._build_ui()
        self._setup_shortcuts()
        self._load_patient_data()
        if self._pending_sample_id and not self._is_existing:
            self.load_sample(self._pending_sample_id)
        elif self._pending_prefill and not self._is_existing:
            self.apply_prefill(self._pending_prefill)

    @staticmethod
    def _generate_patient_id() -> str:
        return f"P-{uuid.uuid4().hex[:8].upper()}"

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.header = QLabel(f"Patient ID: {self._patient_id}")
        set_accessible(self.header, "lbl_patient_record_header")

        header_row = QHBoxLayout()
        header_row.addWidget(self.header)
        header_row.addStretch()
        self.chk_randomize_layout = QCheckBox("Randomize Layout")
        set_accessible(self.chk_randomize_layout, "chk_randomize_layout")
        self.chk_randomize_layout.setToolTip(
            "Simulates pharmacy UI customization. objectName and accessibleName stay the same."
        )
        self.chk_randomize_layout.toggled.connect(self._on_randomize_layout)
        header_row.addWidget(self.chk_randomize_layout)
        layout.addLayout(header_row)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(False)
        self.tab_widget.tabBar().setExpanding(False)
        self.tab_widget.tabBar().setMinimumHeight(32)
        self.tab_widget.setMinimumHeight(520)
        set_accessible(self.tab_widget, "tab_widget_patient", "tab_widget_patient")

        self.general_tab = GeneralTab()
        self.insurance_tab = InsuranceTab()
        self.family_tab = FamilyTab()
        self.allergies_tab = AllergiesTab()
        self.communications_tab = CommunicationsTab()
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.insurance_tab, "Insurance")
        self.tab_widget.addTab(self.family_tab, "Family")
        self.tab_widget.addTab(self.allergies_tab, "Allergies")
        self.tab_widget.addTab(self.communications_tab, "Communications")

        layout.addWidget(self.tab_widget)

        button_row = QHBoxLayout()

        self.btn_load_sample = QPushButton("Load Sample")
        set_accessible(self.btn_load_sample, "btn_load_sample", "btn_load_sample")
        sample_menu = QMenu(self)
        for sample in SAMPLE_PATIENTS:
            action = sample_menu.addAction(sample["label"])
            action.setData(sample["id"])
            action.triggered.connect(
                lambda checked=False, sid=sample["id"]: self.load_sample(sid)
            )
        self.btn_load_sample.setMenu(sample_menu)

        button_row.addWidget(self.btn_load_sample)
        button_row.addStretch()

        self.btn_save = QPushButton("Save")
        set_accessible(self.btn_save, "btn_save", "btn_save")
        self.btn_save.clicked.connect(self._on_save)

        self.btn_update = QPushButton("Update")
        set_accessible(self.btn_update, "btn_update", "btn_update")
        self.btn_update.clicked.connect(self._on_update)

        self.btn_close = QPushButton("Close")
        set_accessible(self.btn_close, "btn_close", "btn_close")
        self.btn_close.clicked.connect(self.close)

        button_row.addWidget(self.btn_save)
        button_row.addWidget(self.btn_update)
        button_row.addWidget(self.btn_close)
        layout.addLayout(button_row)

    def _load_patient_data(self) -> None:
        self.general_tab.set_patient_id(self._patient_id)
        if not self._is_existing:
            return

        patient = self._repository.get_patient(self._patient_id)
        if patient:
            self.general_tab.set_field_values(patient)

        members = self._repository.get_family_members(self._patient_id)
        self.family_tab.set_members(members)

        insurance = self._repository.get_insurance(self._patient_id)
        if insurance:
            self.insurance_tab.set_field_values(insurance)
        else:
            self.insurance_tab.clear_fields()

        self.allergies_tab.set_allergies(self._repository.get_allergies(self._patient_id))

        comm = self._repository.get_communications(self._patient_id)
        if comm.get("preferences") or comm.get("methods"):
            self.communications_tab.set_data(comm)
        else:
            self.communications_tab.clear_fields()

    def load_sample(self, sample_id: str) -> None:
        """Prefill tabs from a test payload."""
        sample = get_sample(sample_id)
        if sample is None:
            show_warning(self, "Load Sample", f"Unknown sample: {sample_id}")
            return

        general = dict(sample["general"])
        general["patient_id"] = self._patient_id
        self.general_tab.set_field_values(general)
        self.family_tab.set_members(sample.get("family", []))
        if "insurance" in sample:
            self.insurance_tab.set_field_values(sample["insurance"])
        else:
            self.insurance_tab.clear_fields()
        self.allergies_tab.set_allergies(sample.get("allergies", []))
        if "communications" in sample:
            self.communications_tab.set_data(sample["communications"])
        else:
            self.communications_tab.clear_fields()
        self.tab_widget.setCurrentIndex(0)
        self.header.setText(f"Patient ID: {self._patient_id}  (sample: {sample['label']})")

    def apply_prefill(self, prefill: dict[str, str]) -> None:
        """Prefill General tab from patient search criteria."""
        data = dict(prefill)
        data["patient_id"] = self._patient_id
        self.general_tab.set_field_values(data)
        self.tab_widget.setCurrentIndex(0)

    def _on_randomize_layout(self, enabled: bool) -> None:
        self.general_tab.set_randomized_layout(enabled)
        self.insurance_tab.set_randomized_layout(enabled)
        self.communications_tab.set_randomized_layout(enabled)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Right"), self, self._next_tab)
        QShortcut(QKeySequence("Ctrl+Left"), self, self._prev_tab)

        for index, (_title, _object_name, letter) in enumerate(TAB_DEFINITIONS):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{letter}"), self)
            shortcut.activated.connect(lambda idx=index: self._go_to_tab(idx))

    def _go_to_tab(self, index: int) -> None:
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def _next_tab(self) -> None:
        count = self.tab_widget.count()
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() + 1) % count)

    def _prev_tab(self) -> None:
        count = self.tab_widget.count()
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() - 1) % count)

    def _focus_field(self, object_name: str) -> None:
        widget = self.general_tab.findChild(QWidget, object_name)
        if widget:
            self.tab_widget.setCurrentIndex(0)
            widget.setFocus()

    def _validate_and_collect(self) -> dict | None:
        values = self.general_tab.get_field_values()
        errors = validate_patient(values)
        if not errors:
            return values

        messages = "\n".join(f"• {err.message}" for err in errors)
        show_warning(self, "Validation", messages)
        self._focus_field(errors[0].object_name)
        return None

    def _persist(self) -> bool:
        values = self._validate_and_collect()
        if values is None:
            return False

        self._repository.save_patient(values)
        self._repository.save_insurance(self._patient_id, self.insurance_tab.get_field_values())
        self._repository.save_family_members(self._patient_id, self.family_tab.get_members())
        self._repository.save_allergies(self._patient_id, self.allergies_tab.get_allergies())
        comm_prefs = self.communications_tab.get_preferences()
        self._repository.save_communications(
            self._patient_id,
            comm_prefs,
            self.communications_tab.get_methods(),
        )
        self._is_existing = True
        return True

    def _on_save(self) -> None:
        if not self._persist():
            return

        values = self.general_tab.get_field_values()
        allergy_count = len(self.allergies_tab.get_allergies())
        method_count = len(self.communications_tab.get_methods())
        show_info(
            self,
            "Save",
            f"Patient ID: {self._patient_id}\n"
            f"Name: {values.get('first_name')} {values.get('last_name')}\n"
            f"Allergies: {allergy_count}\n"
            f"Communication methods: {method_count}\n\n"
            f"Record saved to database.",
        )

    def _on_update(self) -> None:
        if not self._is_existing:
            show_info(self, "Update", "Save the patient first before updating.")
            return

        if not self._persist():
            return

        values = self.general_tab.get_field_values()
        show_info(
            self,
            "Update",
            f"Patient ID: {self._patient_id}\n"
            f"Name: {values.get('first_name')} {values.get('last_name')}\n"
            f"Health Card: {values.get('health_card') or '(none)'}\n\n"
            f"Record updated in database.",
        )

    @property
    def patient_id(self) -> str:
        return self._patient_id
