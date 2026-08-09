import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YT Downloader")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
