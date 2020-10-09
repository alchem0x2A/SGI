"""All the UI classes goes here
"""
from pathlib import Path
import cv2
import json
import subprocess
from collections import deque
import time
import numpy as np
import os

from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QFile, QTimer
# from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5 import uic

from SGI import utils
from SGI.datastructure import ObjectArray


class MainWindow(QWidget):
    def __init__(self,
                 rootdir=Path("./"),
                 image_buffer_size=20):
        super(QWidget, self).__init__()
        self.rootdir = rootdir
        self.load_ui()
        # Add image buffers as deques
        self.buffer_side = deque(maxlen=image_buffer_size)
        self.buffer_top = deque(maxlen=image_buffer_size)

    def load_ui(self):
        path = self.rootdir / "ui" / "control_panel.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()
        # Load parameters for the camera address
        cam_config_file = self.rootdir / "config" / "cameras.json"
        with open(cam_config_file.as_posix()) as f:
            params = json.load(f)
            # pass
        # TODO: change address to address!
        self.button_side_cam.clicked.connect(lambda: self.fun_window_cam(which="side",
                                                                         cam_params=params["side"]))
        self.button_top_cam.clicked.connect(lambda: self.fun_window_cam(which="top",
                                                                        cam_params=params["top"]))
        # address="http://raspberrypi.local:8081"))
        self.button_measurement.clicked.connect(
            lambda: self.fun_window_measure())

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
            img_path = self.rootdir / "icons" / "{}_cam_on.png".format(which)
        else:
            img_path = self.rootdir / "icons" / "{}_cam_off.png".format(which)
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
        if parent is not None:
            self.parent = parent
        self.load_ui()
        if title != "":
            self.setWindowTitle(title)
        # Quick tweak with parent window?
        # TODO: must be better way to solve the button assignment?!
        # which camera to use?
        self.which = which
        self.camera_activated = False
        self.cam_params = cam_params

        # Get address of camera, use int is possible
        address = cam_params["address"]
        self.address = utils.handle_address(address,
                                            self.parent.rootdir)

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
                ret = utils.init_cam(self.cam_params["init_cmd"])
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
        # print(frame.shape)
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
        rootdir = self.parent.rootdir
        path = rootdir / "ui" / "video_window.ui"
        ui_file = QFile(path.as_posix())
        ui_file.open(QFile.ReadOnly)
        uic.loadUi(ui_file, self)
        ui_file.close()


class MeasurementWindow(QWidget):
    def __init__(self, title="", parent=None):
        super(QWidget, self).__init__()
        if parent is not None:
            self.parent = parent
        self.load_ui()
        # Set the field to contain only digits
        self.field_time_interval.setValidator(QDoubleValidator())
        self.field_counts.setValidator(QIntValidator(1, 65536))
        self.field_columns.setValidator(QIntValidator(1, 65536))
        # Simply use array to store?

        # self.images_side = []
        # self.images_top = []
        # self.results = ObjectArray(rows)

        # Which column is activated?
        self.current_column = 0

        # Setup signal
        self.button_measure.clicked.connect(self.start_measure)
        self.button_save.clicked.connect(self.save)

        # Update text field to resize table
        self.field_counts.returnPressed.connect(self.resize_table)
        self.field_columns.returnPressed.connect(self.resize_table)

        # To provide
        self._init_results()
        self._init_table()

    def _get_rows(self):
        return int(self.field_counts.text())

    def _get_cols(self):
        return int(self.field_columns.text())

    def _init_results(self):
        rows = self._get_rows()
        cols = self._get_cols()               # Default rows
        self.results = ObjectArray(rows, cols)

    def _init_table(self):
        self.resize_table()
        self.table.setCurrentCell(0, 0)

    def _enable_controls(self, choice):
        # Enable or diable controls
        for name in ("button_measure",
                     "button_save",
                     "field_time_interval",
                     "field_counts",
                     "table"):
            getattr(self, name).setEnabled(choice)

    def load_ui(self):
        rootdir = self.parent.rootdir
        path = rootdir / "ui" / "experiment_window.ui"
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
        # local_results[0] =  = []
        # local_results[1] = []
        print("Will do with: ", t_interval, total_counts)
        print("Capturing now ........")
        cnt = 0
        current_column = self.table.currentColumn()

        self._enable_controls(False)

        def handler():
            nonlocal cnt
            cnt += 1
            # Update text
            self.text_status.setText(
                "Capturing:\n{0}/{1}".format(cnt, total_counts))
            # try add the last img in the queue,
            # other with add the empty img
            # Left image, right image, test fields
            local_results = [None, None, None]
            try:
                local_results[0] = self.parent.buffer_side[-1]
            except IndexError:
                local_results[0] = utils.gen_empty_img()

            try:
                local_results[1] = self.parent.buffer_top[-1]
            except IndexError:
                local_results[1] = utils.gen_empty_img()

            # TODO: need more elegant code to do it outside
            self.table.setItem(cnt - 1,
                               current_column,
                               QTableWidgetItem("---"))
            self.table.setCurrentCell(cnt - 1,
                                      current_column)
            self.results.set_item(cnt - 1,
                                  current_column,
                                  local_results)
            # print(time.time())
            if cnt >= total_counts:
                # self.button_measure.setEnabled(True)
                # Clear the status
                timer.stop()
                timer.deleteLater()
                cnt = 0
                QTimer.singleShot(1000,
                                  lambda: self.text_status.setText(""))
                # self.images_side.append(local_results[0] = )
                # self.images_top.append(local_results[1])
                self._enable_controls(True)
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
                                                 caption="Choose the name to save")
        fn = Path(filename)
        print(filename, fn)
        save_root = fn.parent
        save_name = fn.name
        self.results.truncate_array()
        self.save_partial(which="side", root=save_root, name=save_name)
        self.save_partial(which="top", root=save_root, name=save_name)

    def save_partial(self, which="side",
                     root=None,
                     name=""):
        # Save images and csv files
        # TODO: remove this testing code
        if root is None:
            root = self.parent.rootdir / "test_ui"
        if not root.is_dir():
            os.makedirs(root)

        img_path = name + "_{which}_R{r}C{c}.bmp"
        # Disable in case save process is long
        # It is a blocking process!
        self._enable_controls(False)
        cnt = 0

        total_r, total_c = self.results.get_max_nonempty()
        total_imgs = total_r * total_c

        def handler():
            nonlocal cnt
            print(which, cnt)
            # images_list = getattr(self, "images_{0}".format(which))
            if which == "side":
                index = 0
            else:
                index = 1
            print(total_r, total_c)
            # Try to save the row and col
            c = cnt // total_r
            r = cnt % total_r
            print(cnt, r, c)
            # img = images_list[c][r]
            if self.results.get_item(r, c) is None:
                img = img = utils.gen_empty_img()
            else:
                img = self.results.get_item(r, c)[index]
                if img is None:
                    img = utils.gen_empty_img()

            rt = utils.save_image(img,
                                  root / img_path.
                                  format(which=which,
                                         r=r,
                                         c=c))

            self.text_status.setText("Saving images {0}\nR{1:03d} C{2:03d}".
                                     format(which,
                                            r,
                                            c))
            cnt += 1
            if cnt >= total_imgs:
                timer.stop()
                timer.deleteLater()
                cnt = 0
                QTimer.singleShot(1000,
                                  lambda: self.text_status.setText(""))
                self._enable_controls(True)
                return
        timer = QTimer()
        timer.timeout.connect(handler)
        timer.start(10)
        # handler("side")
        # handler("top")
        # print("I'm here")

    def resize_table(self):
        """Resize the table and display
        """
        # The table part, very rough function just to make working
        cur_tbl_row_cnt = self.table.rowCount()
        cur_tbl_col_cnt = self.table.columnCount()
        new_tbl_row_cnt = self._get_rows()
        new_tbl_col_cnt = self._get_cols()

        (cur_results_row_max,
         cur_results_col_max) = self.results.get_max_nonempty()

        cur_results_col_max
        # Try to fill in the tables
        rt = self.results.resize_array(new_tbl_row_cnt, new_tbl_col_cnt)
        if rt is False:
            utils.warningbox(self,
                             ("Cannot update the table\n"
                              "From\t{0} --> {1} rows\n"
                              "\t{2} --> {3} columns")
                             .format(cur_tbl_row_cnt,
                                     new_tbl_row_cnt,
                                     cur_tbl_col_cnt,
                                     new_tbl_col_cnt),
                             level=1)
            return False
        self.table.setRowCount(new_tbl_row_cnt)
        self.table.setColumnCount(new_tbl_col_cnt)
        # Set the active cell to the right column of current
        self.table.setCurrentCell(0, cur_results_col_max)
