"""Consistently sized message boxes for Windows."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMessageBox, QWidget

_DEFAULT_WIDTH = 340


def _apply_dialog_sizing(box: QMessageBox, width: int = _DEFAULT_WIDTH) -> None:
    """Keep dialogs readable but not overly wide."""
    box.setTextFormat(Qt.TextFormat.PlainText)
    for label in box.findChildren(QLabel):
        label.setWordWrap(True)
        label.setMinimumWidth(width)
        label.setMaximumWidth(width)


def show_info(parent: QWidget | None, title: str, message: str, width: int = _DEFAULT_WIDTH) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(title)
    box.setInformativeText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    _apply_dialog_sizing(box, width)
    box.exec()


def show_warning(parent: QWidget | None, title: str, message: str, width: int = _DEFAULT_WIDTH) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(title)
    box.setInformativeText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    _apply_dialog_sizing(box, width)
    box.exec()


def ask_yes_no(parent: QWidget | None, title: str, message: str, width: int = _DEFAULT_WIDTH) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(title)
    box.setInformativeText(message)
    box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    box.setDefaultButton(QMessageBox.StandardButton.No)
    _apply_dialog_sizing(box, width)
    return box.exec() == QMessageBox.DialogCode.Accepted
