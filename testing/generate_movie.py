#!!/usr/bin/env python3
"""Usage: python3 generate_movie.py [NAME]
"""
import cv2
import numpy as np

def create_frame(index,
                 name,
                 framerate=30,
                 size=(640, 480)):
    """Create the frame
    """
    image = np.zeros((size[1], size[0], 3),
                     dtype=np.uint8)
    sec_per_frame = 1.0 / framerate
    sec = index * sec_per_frame
    # White
    cv2.putText(image, "{}".format(name), (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    # Yellow
    cv2.putText(image, "Time={:.3f} s".format(sec), (200, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    #
    cv2.putText(image, "Frame={:04d}".format(index), (300, 300),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    return image

def main(name, maxframe=5000):
    if name == "side":
        size = (640, 480)
        rate = 30
    else:
        size = (720, 480)
        rate =25
        
    writer = cv2.VideoWriter("test_{0}.mp4".format(name),
                            cv2.VideoWriter_fourcc(*"mp4v"),
                            rate,
                            size)
    for index in range(maxframe):
        writer.write(create_frame(index, name, rate, size))

    writer.release()
    
if __name__ == '__main__':
    import sys
    name = sys.argv[1]
    main(name, maxframe=5000)
