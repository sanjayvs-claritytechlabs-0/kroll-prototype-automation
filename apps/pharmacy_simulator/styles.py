"""Traditional Windows healthcare application styling."""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


def apply_healthcare_style(app: QApplication) -> None:
    """Apply a classic desktop healthcare look — gray panels, high contrast."""
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(212, 208, 200))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(225, 225, 225))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QMainWindow, QDialog {
            background-color: #d4d0c8;
        }
        QTabWidget::pane {
            border: 1px solid #808080;
            background: #ffffff;
        }
        QTabBar::tab {
            background: #d4d0c8;
            border: 1px solid #808080;
            min-height: 28px;
            padding: 6px 14px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom-color: #ffffff;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #808080;
            margin-top: 14px;
            padding: 16px 8px 8px 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 8px;
            padding: 0 6px;
        }
        QLabel {
            min-height: 22px;
            padding: 2px 0;
        }
        QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit {
            border: 1px solid #7a7a7a;
            min-height: 26px;
            padding: 4px 6px;
            background: #ffffff;
        }
        QComboBox::drop-down {
            width: 20px;
            border-left: 1px solid #7a7a7a;
        }
        QCheckBox {
            min-height: 24px;
            spacing: 6px;
        }
        QLineEdit:read-only {
            background: #ece9e4;
        }
        QPushButton {
            border: 1px solid #7a7a7a;
            padding: 4px 12px;
            background: #e1e1e1;
            min-width: 70px;
        }
        QPushButton:hover {
            background: #eaf6fd;
        }
        QPushButton:pressed {
            background: #cce4f7;
        }
        QToolBar {
            background: #d4d0c8;
            border-bottom: 1px solid #808080;
            spacing: 4px;
            padding: 2px;
        }
        QStatusBar {
            background: #d4d0c8;
            border-top: 1px solid #808080;
        }
        QTableWidget {
            gridline-color: #c0c0c0;
            selection-background-color: #0078d7;
        }
        QHeaderView::section {
            background: #ece9e4;
            border: 1px solid #808080;
            padding: 4px;
        }
        """
    )
