"""Communication method add/edit dialog."""

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

MESSAGE_TYPES = ["", "Refill Reminder", "Pickup Ready", "Prescription Status", "General", "Marketing"]
NOTIFICATION_TYPES = ["", "SMS", "Email", "Phone Call", "Push", "None"]


class CommunicationMethodDialog(QDialog):
    """Modal for communication method Insert / F2 edit."""

    def __init__(self, method: dict[str, str] | None = None, parent=None) -> None:
        super().__init__(parent)
        method = method or {}

        self.setWindowTitle("Communication Method")
        self.setMinimumWidth(440)
        set_accessible(self, "dlg_communication_method", "dlg_communication_method")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.cmb_message_type = QComboBox()
        self.cmb_message_type.addItems(MESSAGE_TYPES)
        self.cmb_message_type.setMinimumHeight(28)
        set_accessible(self.cmb_message_type, "cmb_message_type")
        msg = str(method.get("message_type", ""))
        idx = self.cmb_message_type.findText(msg)
        if idx >= 0:
            self.cmb_message_type.setCurrentIndex(idx)

        self.cmb_notification_type = QComboBox()
        self.cmb_notification_type.addItems(NOTIFICATION_TYPES)
        self.cmb_notification_type.setMinimumHeight(28)
        set_accessible(self.cmb_notification_type, "cmb_notification_type")
        notif = str(method.get("notification_type", ""))
        idx = self.cmb_notification_type.findText(notif)
        if idx >= 0:
            self.cmb_notification_type.setCurrentIndex(idx)

        self.txt_phone_number = QLineEdit(str(method.get("phone_number", "")))
        self.txt_phone_number.setMinimumHeight(28)
        set_accessible(self.txt_phone_number, "txt_comm_phone_number")

        self.txt_email_address = QLineEdit(str(method.get("email_address", "")))
        self.txt_email_address.setMinimumHeight(28)
        set_accessible(self.txt_email_address, "txt_comm_email_address")

        form.addRow("Message Type:", self.cmb_message_type)
        form.addRow("Notification Type:", self.cmb_notification_type)
        form.addRow("Phone Number:", self.txt_phone_number)
        form.addRow("Email Address:", self.txt_email_address)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_btn = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_btn:
            save_btn.setText("Save")
            set_accessible(save_btn, "btn_comm_method_save")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.cmb_message_type.setFocus()

    def _on_accept(self) -> None:
        if not self.cmb_message_type.currentText().strip():
            self.cmb_message_type.setFocus()
            return
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_accept()
            if self.cmb_message_type.currentText().strip():
                return
        super().keyPressEvent(event)

    def get_method(self) -> dict[str, str]:
        return {
            "message_type": self.cmb_message_type.currentText(),
            "notification_type": self.cmb_notification_type.currentText(),
            "phone_number": self.txt_phone_number.text().strip(),
            "email_address": self.txt_email_address.text().strip(),
        }
