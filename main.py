# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from SGI.ui import MainWindow

def main_loop():
    # Set the high DPI display and icons
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # The root dir from the main.py script
    rootdir = Path("./")
    # Mainloop
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
    

if __name__ == "__main__":
    main_loop()

