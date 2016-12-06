"""Capture webcam video using OpenCV, and playback."""

import datetime
import sys
import cv2

import coils
import util
import os
import Tkinter as tk
from pantilthat import *

# Load the BCM V4l2 driver for /dev/video0
os.system('sudo modprobe bcm2835-v4l2')

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
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
startx = (screen_width/2) - (WIDTH/2)
starty = (screen_height/2) - (HEIGHT/2)




cv2.namedWindow(title)
cv2.moveWindow(title, startx, starty)


end = datetime.datetime.now() + datetime.timedelta(seconds=DURATION)
while end > datetime.datetime.now():

    # Take a snapshot, write framerate on it, and display it.
    hello, image = cap.read()
    image = cv2.flip(image, -1)
    fps_text = '{:.2f}, {:.2f}, {:.2f} fps'.format(*framerate.tick())
    util.writeOSD(image, (fps_text,))
    cv2.imshow(title, image)
    cv2.waitKey(1)
