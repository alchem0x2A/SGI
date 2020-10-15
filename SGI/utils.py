"""Collection of useful functions
"""
import cv2
import subprocess
from pathlib import Path
import numpy as np

from PyQt5.QtWidgets import QMessageBox, QDesktopWidget

######### UI-related methods ####################


def get_screen_size():
    """Get the current available screen geometry
    """
    screen = QDesktopWidget().screenGeometry()
    return screen.width(), screen.height()


def move_to_position(w, h, loc=0):
    """Return the x, y position on the window given the `loc`.
       If loc is a tuple, then directly set window center at `loc`,
       Otherwise, loc is an integer from 0 to 8 representing the corners and center:
       0--------1--------2
       |        |        |
       3--------4--------5
       |        |        |
       6--------7--------8
    """
    screen_w, screen_h = get_screen_size()
    try:
        # If loc is a tuple or list
        center_x, center_y = loc
        x = center_x - w / 2.0
        y = center_y - h / 2.0
    except TypeError:
        loc = int(loc)
        x, y = {0: (0, 0),
                1: (screen_w / 2.0 - w / 2.0, 0),
                2: (screen_w - w, 0),
                3: (0, screen_h / 2.0 - h / 2.0),
                4: (screen_w / 2.0 - w / 2.0, screen_h / 2.0 - h / 2.0),
                5: (screen_w - w, screen_h / 2.0 - h / 2.0),
                6: (0, screen_h - h),
                7: (screen_w / 2.0 - w / 2.0, screen_h - h),
                8: (screen_w - w, screen_h - h),
                }[loc]
    return x, y


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


def questionbox(parent, message):
    """Popup a QMessageBox for question choice
    """
    return QMessageBox.question(parent,
                                "Warning",
                                message) == QMessageBox.Yes

######### array-related methods ####################


def add_columns(array, cols=1):
    """Add `cols` new columns to the right-side of the array
    """
    # TODO: error handling
    rows = array.shape[0]
    new_cols = np.empty((rows, cols), dtype=np.object)
    new_array = np.concatenate((array, new_cols),
                               axis=1)
    return new_array


def add_rows(array, rows=1):
    """Add `rows` new rows below the array
    """
    # TODO: error handling
    cols = array.shape[1]
    new_rows = np.empty((rows, cols), dtype=np.object)
    new_array = np.concatenate((array, new_rows),
                               axis=0)
    return new_array


####### Image-related functions ######################


def gen_empty_img(w=640, h=480):
    """Generate a black image
    """
    return np.zeros((h, w, 3), np.uint8)


def save_image(img, path):
    # Give a PIL img matrix and Path
    path = Path(path)
    retcode = cv2.imwrite(path.as_posix(), img)
    return retcode


###### Config-related functions #####################

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


def handle_address(address, rootdir):
    """Handle the address, is it:
       integer camera ?
       local address ?
       streaming url ?
    """
    try:
        address = int(address)
        return address
    except ValueError:
        # If using an online protocol or absolute address
        for protocol in ("/",
                         "http:",
                         "https:",
                         "rtsp:",
                         "rtmp:",):
            if address.lower().startswith(protocol):
                return address

        # Else, it is a relative path
        # Sorry but no windows NT stuff
        rel_path = Path(address).expanduser()
        rootdir = Path(rootdir).absolute()
        full_path = rootdir / rel_path
        return full_path.as_posix()
