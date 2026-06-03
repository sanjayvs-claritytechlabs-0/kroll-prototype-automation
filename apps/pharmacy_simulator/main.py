"""Entry point for the Kroll by Telus Health pharmacy simulator."""

import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication

from apps.pharmacy_simulator.styles import apply_healthcare_style
from apps.pharmacy_simulator.windows.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Kroll by Telus Health")
    app.setOrganizationName("Telus Health")
    apply_healthcare_style(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
