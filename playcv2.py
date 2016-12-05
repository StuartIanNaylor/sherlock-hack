"""Capture webcam video using OpenCV, and playback."""

import datetime
import sys
import cv2

import coils
import util

DEVICE   = 0 #int(sys.argv[1])
WIDTH    = 640 #int(sys.argv[2])
HEIGHT   = 480 #int(sys.argv[3])
DURATION = 30.0 #float(sys.argv[4])

# Monitor framerates for the given seconds past.
framerate = coils.RateTicker((1,5,10))

# Create the OpenCV video capture object.
cap = cv2.VideoCapture(DEVICE)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

# Create the display window.
title = 'playing OpenCV capture'
cv2.namedWindow(title, cv2.cv.CV_WINDOW_NORMAL)

end = datetime.datetime.now() + datetime.timedelta(seconds=DURATION)
while end > datetime.datetime.now():

    # Take a snapshot, write framerate on it, and display it.
    hello, image = cap.read()
    fps_text = '{:.2f}, {:.2f}, {:.2f} fps'.format(*framerate.tick())
    util.writeOSD(image, (fps_text,))
    cv2.imshow(title, image)
    cv2.waitKey(1)
