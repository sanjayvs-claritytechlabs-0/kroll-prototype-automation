"""Communications tab — preferences + methods grid."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.layout.dynamic_layout import clear_layout, shuffle_widgets_in_layout
from apps.pharmacy_simulator.widgets.accessibility import set_accessible
from apps.pharmacy_simulator.widgets.message_boxes import ask_yes_no

LANGUAGES = ["", "English", "French", "Spanish", "Mandarin", "Punjabi", "Other"]
REFILL_TYPES = ["", "Automatic", "Manual", "Call When Ready", "Do Not Refill"]
PICKUP_PREFERENCES = ["", "In Store", "Curbside", "Delivery", "Mail"]

METHOD_COLUMNS = ("Message Type", "Notification Type", "Phone Number", "Email Address")


class CommunicationsTab(QWidget):
    """Language/refill/pickup preferences and communication methods grid."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_accessible(self, "tab_communications", "tab_communications")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._setup_shortcuts()

    def _combo(self, object_name: str, options: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(options)
        combo.setMinimumHeight(28)
        set_accessible(combo, object_name, object_name)
        return combo

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        set_accessible(scroll, "scroll_communications", "scroll_communications")

        content = QWidget()
        set_accessible(content, "content_communications", "content_communications")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        prefs_group = QGroupBox("Communication Preferences")
        set_accessible(prefs_group, "grp_comm_preferences", "grp_comm_preferences")
        prefs_form = QFormLayout(prefs_group)
        prefs_form.setVerticalSpacing(10)

        self.cmb_language = self._combo("cmb_language", LANGUAGES)
        self.cmb_refill_type = self._combo("cmb_refill_type", REFILL_TYPES)
        self.cmb_pickup_preference = self._combo("cmb_pickup_preference", PICKUP_PREFERENCES)

        prefs_form.addRow("Language:", self.cmb_language)
        prefs_form.addRow("Refill Type:", self.cmb_refill_type)
        prefs_form.addRow("Pickup Preference:", self.cmb_pickup_preference)
        layout.addWidget(prefs_group)

        methods_group = QGroupBox("Communication Methods")
        set_accessible(methods_group, "grp_comm_methods", "grp_comm_methods")
        methods_layout = QVBoxLayout(methods_group)

        hint = QLabel("Insert = Add  |  Delete = Remove  |  F2 / Enter / Double-click = Edit")
        set_accessible(hint, "lbl_comm_methods_hint")
        methods_layout.addWidget(hint)

        self.grid = QTableWidget(0, len(METHOD_COLUMNS))
        self.grid.setHorizontalHeaderLabels(METHOD_COLUMNS)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.setAlternatingRowColors(True)
        self.grid.verticalHeader().setVisible(False)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.setMinimumHeight(180)
        self.grid.itemDoubleClicked.connect(lambda _item: self._edit_method())
        set_accessible(self.grid, "grid_communication_methods", "grid_communication_methods")
        methods_layout.addWidget(self.grid)

        button_row = QHBoxLayout()
        self.btn_insert = QPushButton("Insert")
        set_accessible(self.btn_insert, "btn_comm_insert")
        self.btn_insert.clicked.connect(self._add_method)

        self.btn_delete = QPushButton("Delete")
        set_accessible(self.btn_delete, "btn_comm_delete")
        self.btn_delete.clicked.connect(self._delete_method)

        self.btn_edit = QPushButton("Edit (F2)")
        set_accessible(self.btn_edit, "btn_comm_edit")
        self.btn_edit.clicked.connect(self._edit_method)

        button_row.addWidget(self.btn_insert)
        button_row.addWidget(self.btn_delete)
        button_row.addWidget(self.btn_edit)
        button_row.addStretch()
        methods_layout.addLayout(button_row)
        layout.addWidget(methods_group)

        self._content_layout = layout
        self._content = content
        self._grp_prefs = prefs_group
        self._grp_methods = methods_group
        self._randomized_layout = False

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def set_randomized_layout(self, enabled: bool) -> None:
        if enabled == self._randomized_layout:
            return
        self._randomized_layout = enabled
        if enabled:
            shuffle_widgets_in_layout(
                self._content_layout,
                [self._grp_prefs, self._grp_methods],
                host=self._content,
            )
        else:
            clear_layout(self._content_layout, self._content)
            self._content_layout.addWidget(self._grp_prefs)
            self._content_layout.addWidget(self._grp_methods)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key.Key_Insert), self, self._add_method)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self._delete_method)
        QShortcut(QKeySequence(Qt.Key.Key_F2), self, self._edit_method)
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self._edit_method)
        QShortcut(QKeySequence(Qt.Key.Key_Enter), self, self._edit_method)

    def _selected_row(self) -> int:
        rows = self.grid.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _add_method(self) -> None:
        dialog = CommunicationMethodDialog(parent=self)
        if dialog.exec() != CommunicationMethodDialog.DialogCode.Accepted:
            return
        self._append_row(dialog.get_method())

    def _edit_method(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        dialog = CommunicationMethodDialog(self._row_to_method(row), parent=self)
        if dialog.exec() != CommunicationMethodDialog.DialogCode.Accepted:
            return
        self._set_row(row, dialog.get_method())

    def _delete_method(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        msg_type = self.grid.item(row, 0).text() if self.grid.item(row, 0) else ""
        if not ask_yes_no(self, "Delete Method", f"Remove communication method '{msg_type}'?"):
            return
        self.grid.removeRow(row)

    def _append_row(self, method: dict[str, str]) -> None:
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        self._set_row(row, method)
        self.grid.selectRow(row)

    def _set_row(self, row: int, method: dict[str, str]) -> None:
        values = (
            method.get("message_type", ""),
            method.get("notification_type", ""),
            method.get("phone_number", ""),
            method.get("email_address", ""),
        )
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.grid.setItem(row, col, item)

    def _row_to_method(self, row: int) -> dict[str, str]:
        return {
            "message_type": self.grid.item(row, 0).text() if self.grid.item(row, 0) else "",
            "notification_type": self.grid.item(row, 1).text() if self.grid.item(row, 1) else "",
            "phone_number": self.grid.item(row, 2).text() if self.grid.item(row, 2) else "",
            "email_address": self.grid.item(row, 3).text() if self.grid.item(row, 3) else "",
        }

    def get_preferences(self) -> dict[str, str]:
        return {
            "language": self.cmb_language.currentText(),
            "refill_type": self.cmb_refill_type.currentText(),
            "pickup_preference": self.cmb_pickup_preference.currentText(),
        }

    def set_preferences(self, prefs: dict[str, str]) -> None:
        for combo, key in (
            (self.cmb_language, "language"),
            (self.cmb_refill_type, "refill_type"),
            (self.cmb_pickup_preference, "pickup_preference"),
        ):
            text = str(prefs.get(key, ""))
            idx = combo.findText(text)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def get_methods(self) -> list[dict[str, str]]:
        return [self._row_to_method(row) for row in range(self.grid.rowCount())]

    def set_methods(self, methods: list[dict[str, str]]) -> None:
        self.grid.setRowCount(0)
        for method in methods:
            self._append_row(method)

    def clear_fields(self) -> None:
        self.set_preferences({})
        self.set_methods([])

    def get_data(self) -> dict[str, str | list[dict[str, str]]]:
        return {
            "preferences": self.get_preferences(),
            "methods": self.get_methods(),
        }

    def set_data(self, data: dict) -> None:
        self.set_preferences(data.get("preferences", {}))
        self.set_methods(data.get("methods", []))
