import sys
import numpy as np
import time
import cv2
import imagezmq


def main(index):
    # Create an image sender in PUB/SUB (non-blocking) mode
    if int(index) == 0:
        port = 5555
    else:
        port = 6666
    
    sender = imagezmq.ImageSender(connect_to
                                  ='tcp://localhost:{0}'.format(port))

    image_window_name = 'From Sender ' + str(index)
    i = 0
    if int(index) == 0:
        rec = cv2.VideoCapture(0)

    time.sleep(2)
    
    while True:  # press Ctrl-C to stop image sending program
        # Increment a counter and print it's current state to console
        i = i + 1
        print('Sending ' + str(i))

        if int(index) != 0: 
        # Send test image if index =0
        # Create a simple image
            image = np.zeros((400, 400, 3), dtype='uint8')
            green = (0, 255, 0)
            cv2.rectangle(image, (50, 50), (300, 300), green, 5)

            # Add an incrementing counter to the image
            cv2.putText(image, str(i), (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
        else:
            ret, image = rec.read()

        # Send an image to the queue
        sender.send_image(image_window_name, image)
        time.sleep(0.5)

if __name__ == '__main__':
    index = sys.argv[1]
    main(index)

