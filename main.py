# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path


from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt5.QtWidgets import QFileDialog, QMessageBox
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
import numpy as np
import os



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
        # TODO: use the threaded version instead
        ret, frame = self.camera.read()
        #print(ret, frame.shape)
        # If there is no image captured, return False
        # So that the Label is "no preview"
        if frame is None:
            # If ret is False then the image is None
            empty_img = np.zeros((640, 480, 3), np.uint8)
            self.img_buffer.append(empty_img)
            return False
        
        self.img_buffer.append(frame)
        # ret, frame = self.image_hub.recv_image()
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Now add the image data to the buffer_side
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
        if parent is not None:
            self.parent = parent
        
        # Setup signal
        self.button_measure.clicked.connect(self.start_measure)
        self.button_save.clicked.connect(self.save)
        self.button_update.clicked.connect(self.resize_table_column)

        # self.current_column = 0
        

    def enable_controls(self, choice):
        # Enable or diable controls
        for name in ("button_measure",
                     "button_save",
                     "field_time_interval",
                     "field_counts",
                     "table"):
            getattr(self, name).setEnabled(choice)

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
            # Do nothing!

        print("Current column", self.table.currentColumn())
        t_interval = int(self.field_time_interval.text())
        total_counts = int(self.field_counts.text())
        # Local image buffers
        image_col_side = []
        image_col_top = []
        print("Will do with: ", t_interval, total_counts)
        print("Capturing now ........")
        cnt = 0
        current_column = self.table.currentColumn()

        self.enable_controls(False)
        def handler():
            nonlocal cnt
            cnt += 1
            # Update text
            self.text_status.setText("Capturing:\n{0}/{1}".format(cnt, total_counts))
            # try add the last img in the queue,
            # other with add the empty img
            try:
                image_col_side.append(self.parent.buffer_side[-1])
            except IndexError:
                empty_img = np.zeros((640, 480, 3), np.uint8)
                image_col_side.append(empty_img)

            try:
                image_col_top.append(self.parent.buffer_top[-1])
            except IndexError:
                empty_img = np.zeros((640, 480, 3), np.uint8)
                image_col_top.append(empty_img)
                
            # TODO: need more elegant code to do it outside
            self.table.setItem(cnt - 1,
                               current_column,
                               QTableWidgetItem("---"))
            self.table.setCurrentCell(cnt - 1,
                                      current_column)
            # print(time.time())
            if cnt >= total_counts:
                # self.button_measure.setEnabled(True)
                # Clear the status
                timer.stop()
                timer.deleteLater()
                cnt = 0
                QTimer.singleShot(1000,
                                  lambda: self.text_status.setText(""))
                self.images_side.append(image_col_side)
                self.images_top.append(image_col_top)
                self.enable_controls(True)
                self.table.setCurrentCell(0, current_column + 1)
                return
            # self.timer.singleShot(t_interval, handler)
        timer = QTimer()
        timer.timeout.connect(handler)
        timer.start(t_interval)
        return True


    def save(self):
        (filename,
         filetype) = QFileDialog.getSaveFileName(self,
                                                 caption=
                                                 "Choose the name to save")
        fn = Path(filename)
        print(filename, fn)
        save_root = fn.parent
        save_name = fn.name
        self.save_partial(which="side", root=save_root, name=save_name)
        self.save_partial(which="top", root=save_root, name=save_name)
        
    def save_partial(self, which="side",
                     root=None,
                     name=""):
        # Save images and csv files
        # TODO: remove this testing code
        if root is None:
            root = self.parent.curpath / "test_ui"
        if not root.is_dir():
            os.makedirs(root)

        img_path = name + "_{which}_{i}.bmp"
        # Disable in case save process is long
        # It is a blocking process!
        self.enable_controls(False)
        cnt = 0

        def handler():
            nonlocal cnt
            print(which, cnt)
            images_list = getattr(self, "images_{0}".format(which))
            total_c = len(images_list)
            total_r = len(images_list[0])
            # print(which)
            # Use ndarray instead
            total_imgs = len(images_list) * len(images_list[0])
            if cnt >= total_imgs:
                timer.stop()
                timer.deleteLater()
                cnt  = 0
                QTimer.singleShot(1000,
                                  lambda: self.text_status.setText(""))
                self.enable_controls(True)
                return
            c = cnt // total_r
            r = cnt % total_r
            print(total_c, total_r, c, r)
            img = images_list[c][r]
            cnt += 1
            rt = save_image(img,
                            root / img_path.format(which=which,
                                                   i=cnt))
            self.text_status.setText("Saving images {0}\n{1}/{2}".
                                     format(which,
                                            cnt,
                                            total_imgs))
        timer = QTimer()
        timer.timeout.connect(handler)
        timer.start(10)
        # handler("side")
        # handler("top")
        # print("I'm here")

        
    def resize_table_column(self):
        """Resize the table if possible
        """
        # cur_col_cnt = self.table.columnCount()
        cur_row_cnt = self.table.rowCount()
        new_row_cnt = int(self.field_counts.text())
        if new_row_cnt < cur_row_cnt:
            warningbox(self,
                       ("Cannot update the table\n"
                        "New row counts are less than current"),
                       level=1)
            return False
        self.table.setRowCount(new_row_cnt)
        
        

def main_loop():
    # Set the high DPI display and icons
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # Mainloop
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
    
    
    
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


def warningbox(parent, message, level=0):
    """Popup a QMessageBox for warning information
       levels: 
       0 --- normal message (about)
       1 --- warning message
       2 --- error (critical)
    """
    if level == 0:
        QMessageBox.about(parent, "", message)
    elif level == 1:
        QMessageBox.warning(parent, "Warning", message)
    else:
        QMessageBox.critical(parent, "Error", message)
        


if __name__ == "__main__":
    main_loop()

