"""Collection of useful functions
"""
import cv2
import subprocess
from pathlib import Path
import numpy as np

from PyQt5.QtWidgets import QMessageBox, QDesktopWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

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


def set_transparent(img):
    """Convert white field in RGBA to transparent
       img should be an rgba or bgra image
    """
    assert img.shape[-1] == 4
    white_pix = np.all(img == [255, 255, 255, 255], axis=-1)
    # print(white_pix)
    img[white_pix, -1] = 0
    # return img


def img_to_pixmap(img, scale=1.0, code="rgb"):
    """Convert an opencv image array to QPixmap
       return: QPixmap, (width, height)
    """
    if code.lower() == "rgb":
        img_format = QImage.Format_RGB888
        bytes_per_pixel = 3         # For RGB
    elif code.lower() == "bgr":
        img_format = QImage.Format_BGR888
        bytes_per_pixel = 3         # for bgr
    elif code.lower() == "rgba":
        img_format = QImage.Format_RGBA8888
        bytes_per_pixel = 4
    else:
        img_format = QImage.Format_Grayscale8
        bytes_per_pixel = 1
    # Need to fix the problem with background
    qimg = QImage(img, img.shape[1], img.shape[0],
                  img.shape[1] * bytes_per_pixel,
                  img_format)
    width = img.shape[1]
    height = img.shape[0]
    w_ = int(width * scale)
    h_ = int(height * scale)
    if w_ > h_:
        pix = QPixmap.fromImage(qimg).scaledToWidth(
            w_, mode=Qt.SmoothTransformation)
    else:
        pix = QPixmap.fromImage(qimg).scaledToHeight(
            h_, mode=Qt.SmoothTransformation)
    return pix, (w_, h_)


def generate_ruler(length=640, height=30, dpp=4, side="x"):
    """Generate a pixmap instance for the video image
       ddp: distance per pixel 
    """
    font = cv2.FONT_HERSHEY_PLAIN
    line = cv2.LINE_AA
    black = (0, 0, 0)
    height = height
    img = np.ones((height, length, 3), np.uint8) * 255  # white image

    def _draw_ruler(positions, texts, thickness=2):
        """Positions are the main ticks
        """
        # draw main line
        cv2.line(img, (0, 0), (length, 0), black, thickness, line)
        # draw main ticks
        for i, (p, s) in enumerate(zip(positions, texts)):
            cv2.line(img, (p, 0), (p, 10), black, thickness, line)
            (w, h), f = cv2.getTextSize(s, font, 1, 1)
            # Align the text
            if i == 0:
                # First align on left
                pp = p
            elif i < len(positions) - 1:
                # Other align on center
                pp = p - w // 2
            else:
                # Try to make on the right most
                pp = min(length - w, p - w // 2)
            cv2.putText(img, s, (pp, 24), font, 1, black, 1, line)

    def _get_best_grading():
        """Get best grading and text
        """
        possible_main_grading = np.array([10, 20, 25, 40, 50,
                                          100, 200, 250, 400,
                                          500, 1000])
        total_dist = length * dpp
        # Get the most suitable grading
        num_gradings = total_dist / possible_main_grading
        best_grading = possible_main_grading[num_gradings <= 7][0]
        best_num = num_gradings[num_gradings <= 7][0]
        dist = np.arange(best_num) * best_grading
        pos = (dist / dpp).astype(np.int)
        texts = ["{0:d}".format(int(d)) for d in dist]
        return pos, texts

    _draw_ruler(*_get_best_grading())

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    set_transparent(img)
    if side == "x":
        return img
    else:
        return cv2.rotate(img, cv2.cv2.ROTATE_90_CLOCKWISE)


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
