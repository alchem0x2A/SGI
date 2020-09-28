# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path


from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QFile, Qt
from PyQt5 import uic


class MainWindow(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.load_ui()

    def load_ui(self):
        curpath = Path(__file__).parent
        path = curpath / "ui" / "control_panel.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()

if __name__ == "__main__":
    # Set the high DPI display and icons
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # Mainloop
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
