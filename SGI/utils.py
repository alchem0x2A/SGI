"""Collection of useful functions
"""
import cv2
import subprocess
from pathlib import Path
import numpy as np

from PyQt5.QtWidgets import QMessageBox

######### UI-related methods ####################


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
