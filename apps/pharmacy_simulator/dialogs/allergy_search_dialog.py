"""Search and select an allergy from the catalog."""

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

from apps.pharmacy_simulator.data.allergy_catalog import load_allergy_catalog, search_allergies
from apps.pharmacy_simulator.widgets.accessibility import set_accessible


class AllergySearchDialog(QDialog):
    """Step 1 of add allergy: search catalog and select."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_allergy = ""
        self._catalog = load_allergy_catalog()

        self.setWindowTitle("Search Allergy")
        self.setMinimumSize(460, 420)
        set_accessible(self, "dlg_allergy_search", "dlg_allergy_search")

        layout = QVBoxLayout(self)

        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        set_accessible(search_label, "lbl_allergy_search")
        self.txt_search = QLineEdit()
        self.txt_search.setMinimumHeight(28)
        set_accessible(self.txt_search, "txt_allergy_search")
        self.txt_search.textChanged.connect(self._refresh_list)
        self.txt_search.returnPressed.connect(self._accept_selection)
        search_row.addWidget(search_label)
        search_row.addWidget(self.txt_search)
        layout.addLayout(search_row)

        self.list_allergies = QListWidget()
        set_accessible(self.list_allergies, "list_allergy_search_results")
        self.list_allergies.itemDoubleClicked.connect(self._accept_selection)
        layout.addWidget(self.list_allergies)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            set_accessible(ok_btn, "btn_allergy_search_ok")
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_list()
        self.txt_search.setFocus()

    def _refresh_list(self) -> None:
        query = self.txt_search.text()
        matches = search_allergies(query, self._catalog)
        self.list_allergies.clear()
        for name in matches:
            item = QListWidgetItem(name)
            self.list_allergies.addItem(item)

    def _accept_selection(self) -> None:
        item = self.list_allergies.currentItem()
        if item is None:
            return
        self._selected_allergy = item.text()
        self.accept()

    @property
    def selected_allergy(self) -> str:
        return self._selected_allergy
