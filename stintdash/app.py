import sys

from PySide6.QtWidgets import QApplication

from stintdash.main_window import MainWindow
from stintdash.styles import APP_STYLESHEET


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("StintDash")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()
