"""Allergy information form — source, date, comments."""

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
)

from apps.pharmacy_simulator.widgets.accessibility import set_accessible

SOURCES = ["", "Patient", "Prescriber", "Pharmacy", "Other"]


class AllergyInfoDialog(QDialog):
    """Step 2 of add/edit allergy: details form."""

    def __init__(self, allergy_name: str, allergy: dict[str, str] | None = None, parent=None) -> None:
        super().__init__(parent)
        allergy = allergy or {}

        self.setWindowTitle("Allergy Information")
        self.setMinimumWidth(460)
        set_accessible(self, "dlg_allergy_info", "dlg_allergy_info")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.txt_allergy_name = QLineEdit(allergy_name or str(allergy.get("allergy_name", "")))
        self.txt_allergy_name.setReadOnly(True)
        self.txt_allergy_name.setMinimumHeight(28)
        set_accessible(self.txt_allergy_name, "txt_allergy_name")

        self.cmb_source = QComboBox()
        self.cmb_source.addItems(SOURCES)
        self.cmb_source.setMinimumHeight(28)
        set_accessible(self.cmb_source, "cmb_allergy_source")
        source = str(allergy.get("source", "Patient"))
        idx = self.cmb_source.findText(source)
        if idx >= 0:
            self.cmb_source.setCurrentIndex(idx)

        self.txt_date_reported = QDateEdit()
        self.txt_date_reported.setCalendarPopup(True)
        self.txt_date_reported.setDisplayFormat("yyyy-MM-dd")
        self.txt_date_reported.setDate(QDate.currentDate())
        self.txt_date_reported.setMinimumHeight(28)
        set_accessible(self.txt_date_reported, "txt_allergy_date_reported")
        reported = str(allergy.get("date_reported", ""))
        if reported:
            parsed = QDate.fromString(reported, "yyyy-MM-dd")
            if parsed.isValid():
                self.txt_date_reported.setDate(parsed)

        self.txt_comments = QPlainTextEdit(str(allergy.get("comments", "")))
        self.txt_comments.setMinimumHeight(80)
        set_accessible(self.txt_comments, "txt_allergy_comments")

        form.addRow("Allergy Name:", self.txt_allergy_name)
        form.addRow("Source:", self.cmb_source)
        form.addRow("Date Reported:", self.txt_date_reported)
        form.addRow("Comments:", self.txt_comments)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_btn = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_btn:
            save_btn.setText("Save")
            set_accessible(save_btn, "btn_allergy_info_save")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            return
        super().keyPressEvent(event)

    def get_allergy(self) -> dict[str, str]:
        return {
            "allergy_name": self.txt_allergy_name.text().strip(),
            "source": self.cmb_source.currentText(),
            "date_reported": self.txt_date_reported.date().toString("yyyy-MM-dd"),
            "comments": self.txt_comments.toPlainText().strip(),
        }
