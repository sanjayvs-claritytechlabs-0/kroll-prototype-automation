"""Reusable placeholder for tabs not yet implemented."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from apps.pharmacy_simulator.widgets.accessibility import set_accessible


class PlaceholderTab(QWidget):
    """Stub tab shown until full implementation is complete."""

    def __init__(self, tab_name: str, object_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        set_accessible(self, object_name, object_name)

        layout = QVBoxLayout(self)
        label = QLabel(f"{tab_name} — implementation pending (Module 2+)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_accessible(label, f"lbl_{object_name}_placeholder")
        layout.addWidget(label)
