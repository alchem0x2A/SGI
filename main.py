# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path


from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import QFile, Qt, QTimer
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5 import uic

import cv2
import json
import subprocess
from collections import deque
import time



class MainWindow(QWidget):
    def __init__(self, image_buffer_size=20):
        super(QWidget, self).__init__()
        self.load_ui()
        # Add image buffers as deques
        self.buffer_side = deque(maxlen=image_buffer_size)
        self.buffer_top = deque(maxlen=image_buffer_size)

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
        # TODO: How to remove the window instance?
        self.windows_measurement.append(new_window)
        new_window.show()
        print(self.windows_measurement)

    def start_measurement(self):
        pass

    
        

            
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

        self.img_buffer = getattr(self.parent,
                                  "buffer_{which}".format(which=which))


    
        
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
        #print(ret, frame.shape)
        # If there is no image captured, return False
        # So that the Label is "no preview"
        if ret is False:
            return False
        # ret, frame = self.image_hub.recv_image()
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Now add the image data to the buffer_side
        self.img_buffer.append(frame)
        #print(frame.shape)
        # OpenCV used BGR format!
        img = QImage(frame, frame.shape[1],
                     frame.shape[0],
                     QImage.Format_BGR888)
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
        # Set the field to contain only digits
        self.field_time_interval.setValidator(QDoubleValidator())
        self.field_counts.setValidator(QIntValidator())
        # Simply use array to store?
        self.images_side = []
        self.images_top = []
        self.results = []
        # Which column is activated?
        self.current_column = 0
        self.locked = False
        self.timer = QTimer()
        if parent is not None:
            self.parent = parent
        
        # Setup signal
        self.button_measure.clicked.connect(self.start_measure)
        self.button_save.clicked.connect(self.save)

    def load_ui(self):
        curpath = Path(__file__).parent
        path = curpath / "ui" / "experiment_window.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()

    def start_measure(self):
        # Start the measurement
        # Should not return error since Validators used
        # TODO: add a thread lock to block further data acq
        if self.locked:
            # Do nothing!
            return False
        
        t_interval = int(self.field_time_interval.text())
        total_counts = int(self.field_counts.text())
        # Local image buffers
        images_side = []
        images_top = []
        print("Will do with: ", t_interval, total_counts)
        print("Capturing now ........")
        cnt = 0
        self.locked = True

        def handler():
            self.button_measure.setEnabled(False)
            nonlocal cnt
            cnt += 1
            # Update text
            self.text_status.setText("Capturing:\n {0}/{1}".format(cnt, total_counts))
            # print("{}:{}".format(cnt, total_counts))
            # try to get images from buffer, no popping
            images_side.append(self.parent.buffer_side[-1])
            images_top.append(self.parent.buffer_top[-1])
            if cnt >= total_counts:
                self.button_measure.setEnabled(True)
                # Clear the status
                self.timer.singleShot(1000, lambda: self.text_status.setText(""))
                return
            self.timer.singleShot(t_interval, handler)

        handler()
        # Presumably should stop by now?
        print(len(self.images_side),
              len(self.images_top))
        
        # Release the lock
        self.locked = False
        # TODO: how to make column ?
        self.images_side = images_side
        self.images_top = images_top
        return True

    def save(self):
        # Save images and csv files
        print(self.images_side, len(self.images_side))
        print(self.images_top, len(self.images_top))
        # TODO: remove this testing code
        root = self.parent.curpath / "test_ui"
        img_path = "img_{which}_{i}.bmp"
        for i, img in enumerate(self.images_side):
            rt = save_image(img,
                            root / img_path.format(which="side",
                                                   i=i))
            print(rt, i)
        for i, img in enumerate(self.images_top):
            rt = save_image(img,
                            root / img_path.format(which="top",
                                                   i=i))
            print(rt, i)
        
        
        

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

def save_image(img, path):
    # Give a PIL img matrix and Path
    path = Path(path)
    retcode = cv2.imwrite(path.as_posix(), img)
    return retcode
    
if __name__ == "__main__":
    main_loop()

