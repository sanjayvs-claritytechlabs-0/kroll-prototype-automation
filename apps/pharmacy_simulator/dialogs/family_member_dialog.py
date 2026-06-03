"""Add / edit family member modal."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from apps.pharmacy_simulator.widgets.accessibility import set_accessible

RELATIONSHIPS = ["", "Spouse", "Child", "Parent", "Sibling", "Guardian", "Other"]


class FamilyMemberDialog(QDialog):
    """Modal form for family member Insert / F2 edit."""

    def __init__(
        self,
        member: dict[str, str] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Family Member")
        self.setMinimumWidth(420)
        set_accessible(self, "dlg_family_member", "dlg_family_member")

        member = member or {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.txt_member_patient_id = QLineEdit(str(member.get("member_patient_id", "")))
        self.txt_member_patient_id.setMinimumHeight(28)
        set_accessible(self.txt_member_patient_id, "txt_member_patient_id")

        self.txt_name = QLineEdit(str(member.get("name", "")))
        self.txt_name.setMinimumHeight(28)
        set_accessible(self.txt_name, "txt_member_name")

        self.cmb_relationship = QComboBox()
        self.cmb_relationship.addItems(RELATIONSHIPS)
        self.cmb_relationship.setMinimumHeight(28)
        set_accessible(self.cmb_relationship, "cmb_member_relationship")
        rel = str(member.get("relationship", ""))
        idx = self.cmb_relationship.findText(rel)
        if idx >= 0:
            self.cmb_relationship.setCurrentIndex(idx)

        form.addRow("Patient ID:", self.txt_member_patient_id)
        form.addRow("Name:", self.txt_name)
        form.addRow("Relationship:", self.cmb_relationship)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_btn = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_btn:
            save_btn.setText("Save")
            set_accessible(save_btn, "btn_family_member_save")
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            set_accessible(cancel_btn, "btn_family_member_cancel")

        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.txt_name.setFocus()

    def _on_accept(self) -> None:
        if not self.txt_name.text().strip():
            self.txt_name.setFocus()
            return
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_accept()
            if self.txt_name.text().strip():
                return
        super().keyPressEvent(event)

    def get_member(self) -> dict[str, str]:
        return {
            "member_patient_id": self.txt_member_patient_id.text().strip(),
            "name": self.txt_name.text().strip(),
            "relationship": self.cmb_relationship.currentText(),
        }
