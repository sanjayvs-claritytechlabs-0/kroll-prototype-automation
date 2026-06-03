"""Family tab — linked family members grid."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.dialogs.family_member_dialog import FamilyMemberDialog
from apps.pharmacy_simulator.widgets.accessibility import set_accessible

COLUMNS = ("Patient ID", "Name", "Relationship")


class FamilyTab(QWidget):
    """Family members grid with Insert / Delete / F2 / Enter workflows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_accessible(self, "tab_family", "tab_family")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        hint = QLabel("Insert = Add  |  Delete = Remove  |  F2 / Enter = Edit  |  Double-click = Edit")
        set_accessible(hint, "lbl_family_hint")
        layout.addWidget(hint)

        self.grid = QTableWidget(0, len(COLUMNS))
        self.grid.setHorizontalHeaderLabels(COLUMNS)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.setAlternatingRowColors(True)
        self.grid.verticalHeader().setVisible(False)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.itemDoubleClicked.connect(lambda _item: self._edit_member())
        set_accessible(self.grid, "grid_family", "grid_family")
        layout.addWidget(self.grid)

        button_row = QHBoxLayout()
        self.btn_insert = QPushButton("Insert")
        set_accessible(self.btn_insert, "btn_family_insert")
        self.btn_insert.clicked.connect(self._add_member)

        self.btn_delete = QPushButton("Delete")
        set_accessible(self.btn_delete, "btn_family_delete")
        self.btn_delete.clicked.connect(self._delete_member)

        self.btn_edit = QPushButton("Edit (F2)")
        set_accessible(self.btn_edit, "btn_family_edit")
        self.btn_edit.clicked.connect(self._edit_member)

        button_row.addWidget(self.btn_insert)
        button_row.addWidget(self.btn_delete)
        button_row.addWidget(self.btn_edit)
        button_row.addStretch()
        layout.addLayout(button_row)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key.Key_Insert), self, self._add_member)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self._delete_member)
        QShortcut(QKeySequence(Qt.Key.Key_F2), self, self._edit_member)
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self._edit_member)
        QShortcut(QKeySequence(Qt.Key.Key_Enter), self, self._edit_member)

    def _selected_row(self) -> int:
        rows = self.grid.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _add_member(self) -> None:
        dialog = FamilyMemberDialog(parent=self)
        if dialog.exec() != FamilyMemberDialog.DialogCode.Accepted:
            return
        self._append_row(dialog.get_member())

    def _edit_member(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        dialog = FamilyMemberDialog(self._row_to_member(row), parent=self)
        if dialog.exec() != FamilyMemberDialog.DialogCode.Accepted:
            return
        self._set_row(row, dialog.get_member())

    def _delete_member(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        name = self.grid.item(row, 1).text() if self.grid.item(row, 1) else ""
        answer = QMessageBox.question(
            self,
            "Delete Family Member",
            f"Remove family member '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.grid.removeRow(row)

    def _append_row(self, member: dict[str, str]) -> None:
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        self._set_row(row, member)
        self.grid.selectRow(row)

    def _set_row(self, row: int, member: dict[str, str]) -> None:
        values = (
            member.get("member_patient_id", ""),
            member.get("name", ""),
            member.get("relationship", ""),
        )
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.grid.setItem(row, col, item)

    def _row_to_member(self, row: int) -> dict[str, str]:
        return {
            "member_patient_id": self.grid.item(row, 0).text() if self.grid.item(row, 0) else "",
            "name": self.grid.item(row, 1).text() if self.grid.item(row, 1) else "",
            "relationship": self.grid.item(row, 2).text() if self.grid.item(row, 2) else "",
        }

    def get_members(self) -> list[dict[str, str]]:
        members: list[dict[str, str]] = []
        for row in range(self.grid.rowCount()):
            members.append(self._row_to_member(row))
        return members

    def set_members(self, members: list[dict[str, str]]) -> None:
        self.grid.setRowCount(0)
        for member in members:
            self._append_row(member)
