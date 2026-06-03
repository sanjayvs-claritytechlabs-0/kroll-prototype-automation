"""Allergies tab — grid with search/add modal flow."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.pharmacy_simulator.dialogs.allergy_info_dialog import AllergyInfoDialog
from apps.pharmacy_simulator.dialogs.allergy_search_dialog import AllergySearchDialog
from apps.pharmacy_simulator.widgets.accessibility import set_accessible
from apps.pharmacy_simulator.widgets.message_boxes import ask_yes_no

COLUMNS = ("Allergy Name", "Source", "Date Reported", "Comments")


class AllergiesTab(QWidget):
    """Allergies grid: Insert → search → info form → save row."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_accessible(self, "tab_allergies", "tab_allergies")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        hint = QLabel(
            "Insert = Search & Add  |  Delete = Remove  |  F2 / Enter / Double-click = Edit"
        )
        set_accessible(hint, "lbl_allergies_hint")
        layout.addWidget(hint)

        self.grid = QTableWidget(0, len(COLUMNS))
        self.grid.setHorizontalHeaderLabels(COLUMNS)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.setAlternatingRowColors(True)
        self.grid.verticalHeader().setVisible(False)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.itemDoubleClicked.connect(lambda _item: self._edit_allergy())
        set_accessible(self.grid, "grid_allergies", "grid_allergies")
        layout.addWidget(self.grid)

        button_row = QHBoxLayout()
        self.btn_insert = QPushButton("Insert")
        set_accessible(self.btn_insert, "btn_allergies_insert")
        self.btn_insert.clicked.connect(self._add_allergy)

        self.btn_delete = QPushButton("Delete")
        set_accessible(self.btn_delete, "btn_allergies_delete")
        self.btn_delete.clicked.connect(self._delete_allergy)

        self.btn_edit = QPushButton("Edit (F2)")
        set_accessible(self.btn_edit, "btn_allergies_edit")
        self.btn_edit.clicked.connect(self._edit_allergy)

        button_row.addWidget(self.btn_insert)
        button_row.addWidget(self.btn_delete)
        button_row.addWidget(self.btn_edit)
        button_row.addStretch()
        layout.addLayout(button_row)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence(Qt.Key.Key_Insert), self, self._add_allergy)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self._delete_allergy)
        QShortcut(QKeySequence(Qt.Key.Key_F2), self, self._edit_allergy)
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self._edit_allergy)
        QShortcut(QKeySequence(Qt.Key.Key_Enter), self, self._edit_allergy)

    def _selected_row(self) -> int:
        rows = self.grid.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _add_allergy(self) -> None:
        search = AllergySearchDialog(parent=self)
        if search.exec() != AllergySearchDialog.DialogCode.Accepted:
            return
        allergy_name = search.selected_allergy
        if not allergy_name:
            return

        info = AllergyInfoDialog(allergy_name, parent=self)
        if info.exec() != AllergyInfoDialog.DialogCode.Accepted:
            return
        self._append_row(info.get_allergy())

    def _edit_allergy(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        existing = self._row_to_allergy(row)
        info = AllergyInfoDialog(existing["allergy_name"], existing, parent=self)
        if info.exec() != AllergyInfoDialog.DialogCode.Accepted:
            return
        self._set_row(row, info.get_allergy())

    def _delete_allergy(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        name = self.grid.item(row, 0).text() if self.grid.item(row, 0) else ""
        if not ask_yes_no(self, "Delete Allergy", f"Remove allergy '{name}'?"):
            return
        self.grid.removeRow(row)

    def _append_row(self, allergy: dict[str, str]) -> None:
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        self._set_row(row, allergy)
        self.grid.selectRow(row)

    def _set_row(self, row: int, allergy: dict[str, str]) -> None:
        values = (
            allergy.get("allergy_name", ""),
            allergy.get("source", ""),
            allergy.get("date_reported", ""),
            allergy.get("comments", ""),
        )
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.grid.setItem(row, col, item)

    def _row_to_allergy(self, row: int) -> dict[str, str]:
        return {
            "allergy_name": self.grid.item(row, 0).text() if self.grid.item(row, 0) else "",
            "source": self.grid.item(row, 1).text() if self.grid.item(row, 1) else "",
            "date_reported": self.grid.item(row, 2).text() if self.grid.item(row, 2) else "",
            "comments": self.grid.item(row, 3).text() if self.grid.item(row, 3) else "",
        }

    def get_allergies(self) -> list[dict[str, str]]:
        return [self._row_to_allergy(row) for row in range(self.grid.rowCount())]

    def set_allergies(self, allergies: list[dict[str, str]]) -> None:
        self.grid.setRowCount(0)
        for allergy in allergies:
            self._append_row(allergy)
