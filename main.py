# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path


from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import QFile, Qt, QTimer
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5 import uic

import cv2
import json
import subprocess


class MainWindow(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.load_ui()
        

    def load_ui(self):
        self.curpath = Path(__file__).parent
        path = self.curpath / "ui" / "control_panel.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()
        # Load parameters for the camera address
        cam_config_file = self.curpath / "config" / "cameras.json"
        with open(cam_config_file.as_posix()) as f:
            params = json.load(f)
                # pass
        # TODO: change address to address!
        self.button_side_cam.clicked.connect(lambda: self.fun_window_cam(which="side",
                                                                         cam_params=params["side"]))
        self.button_top_cam.clicked.connect(lambda: self.fun_window_cam(which="top",
                                                                        cam_params=params["top"]))
                                                                        #address="http://raspberrypi.local:8081"))
        self.button_measurement.clicked.connect(lambda: self.fun_window_measure())


    def fun_window_cam(self, which, cam_params={}):
        assert which in ("side", "top")
        # Start a side cam window
        window_name = "window_{}_cam".format(which)
           
        if not hasattr(self, window_name):
            setattr(self, window_name,
                    VideoWindow(title="{} Camera".format(which.capitalize()),
                                parent=self,
                                which=which,
                                cam_params=cam_params))
                                
        # If window not visible then show it
        win_obj = getattr(self, window_name)
        if not win_obj.isVisible():
            win_obj.show()


    def switch_cam_state(self, which):
        # Provide which for either side or top ?
        assert which in ("side", "top")
        button = getattr(self, "button_{}_cam".format(which))
        window = getattr(self, "window_{}_cam".format(which))
        if window.camera_activated:
            img_path = self.curpath / "icons" / "{}_cam_on.png".format(which)
        else:
            img_path = self.curpath / "icons" / "{}_cam_off.png".format(which)
        button.setIcon(QIcon(img_path.as_posix()))

    def fun_window_measure(self):
        # Open an window instance of measurement series
        # and add to the self.windows_measurement list
        if not hasattr(self, "windows_measurement"):
            self.windows_measurement = []
        new_window = MeasurementWindow(title="",
                                       parent=self)
        self.windows_measurement.append(new_window)
        new_window.show()
        

            
class VideoWindow(QWidget):
    def __init__(self, title="",
                 parent=None,
                 which="",
                 cam_params={}):
        super(QWidget, self).__init__()
        self.load_ui()
        if title != "":
            self.setWindowTitle(title)
        # Quick tweak with parent window?
        if parent is not None:
            self.parent = parent
        # TODO: must be better way to solve the button assignment?!
        # which camera to use?
        self.which = which
        self.camera_activated = False
        self.cam_params = cam_params
        
        # Get address of camera, use int is possible 
        address = cam_params["address"]
        try:
            address = int(address)
        except ValueError:
            pass
        self.address = address
        
        # Set FPS; Possibly to a lower number if Video is Slaggy 
        try:
            fps = int(cam_params["fps"])
        except ValueError:
            fps = 30
        self.fps = fps
        

        # Turn on and off video preview
        self.radio_preview.toggled.connect(self.toggle_preview)
        self.camera = cv2.VideoCapture(self.address)
        self.camera_initialized = self.camera.isOpened()
        print(self.address, self.camera)
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)


    
        
    # Turn on and off
    def toggle_preview(self):
        # TODO: add state check for error in video
        if self.radio_preview.isChecked():
            # If camera not initialized, try to use the cam_params["init_cmd"]
            if not self.camera_initialized:
                ret = init_cam(self.cam_params["init_cmd"])
                if ret is False:
                    self.radio_preview.setChecked(False)
            
            if self.camera_initialized:
                print("Preview !")
                self.camera_activated = True
                self.timer.start(int(1000 / self.fps))
        else:
            print("No preview")
            self.camera_activated = False
            # Stop the timer
            self.timer.stop()
            # self.video_frame.setPixmap(QPixmap())
            self.video_frame.setText("No Preview Available")
            self.video_frame.adjustSize()
            # self.adjustSize()
        self.parent.switch_cam_state(self.which)

    def next_frame(self):
        # Net frame?
        ret, frame = self.camera.read()
        print(ret, frame)
        # If there is no image captured, return False
        # So that the Label is "no preview"
        if ret is False:
            return False
        # ret, frame = self.image_hub.recv_image()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #print(frame.shape)
        img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        # TODO: Check if resizing really works
        self.video_frame.setPixmap(pix)
        self.video_frame.adjustSize()
        return True
        

    def load_ui(self):
        curpath = Path(__file__).parent
        path = curpath / "ui" / "video_window.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()


class MeasurementWindow(QWidget):
    def __init__(self, title="", parent=None):
        super(QWidget, self).__init__()
        self.load_ui()
        if parent is not None:
            self.parent = parent

    def load_ui(self):
        curpath = Path(__file__).parent
        path = curpath / "ui" / "experiment_window.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()


def main_loop():
    # Set the high DPI display and icons
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # Mainloop
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    app.exec_()
    
    
    
######## OOP-independent functions ###########
######## To be moved to other libs ###########
def init_cam(cmd):
    """Use subprocess to execute a command, if needed to activate the camera
    """
    cmd = cmd.strip()
    if len(cmd) > 0:
        print("Executing the activating cmd:")
        print(cmd)
        print("---------Output from process--------------")
        proc = subprocess.run(cmd, shell=True)
        return proc.returncode == 0
    else:
        # No command provided
        return -1
    
if __name__ == "__main__":
    main_loop()

