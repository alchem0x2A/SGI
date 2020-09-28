# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path


from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
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
        self.button_side_cam.clicked.connect(self.fun_window_side_cam)
        self.button_top_cam.clicked.connect(self.fun_window_top_cam)

    def fun_window_side_cam(self):
        # Start a side cam window
        if not hasattr(self, "window_side_cam"):
            self.window_side_cam = VideoWindow(title="Side Camera")
        self.window_side_cam.show()

    def fun_window_top_cam(self):
        # Start a side cam window
        if not hasattr(self, "window_top_cam"):
            self.window_top_cam = VideoWindow(title="Top Camera")
        self.window_top_cam.show()

            
class VideoWindow(QWidget):
    def __init__(self, title=""):
        super(QWidget, self).__init__()
        self.load_ui()
        if title != "":
            self.setWindowTitle(title)

    def load_ui(self):
        curpath = Path(__file__).parent
        path = curpath / "ui" / "video_window.ui"
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
