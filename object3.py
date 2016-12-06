"""Object detection pipeline."""

import multiprocessing
import datetime
import time
import sys
import cv2
import numpy as np
import socket
import Tkinter as tk

import sharedmem
import mpipe

import coils
import util
import os
from pantilthat import *

# Load the BCM V4l2 driver for /dev/video0
os.system('sudo modprobe bcm2835-v4l2')



DEVICE   = 0 #int(sys.argv[1])
WIDTH    = 1024 #int(sys.argv[2])
HEIGHT   = 768 #int(sys.argv[3])
DURATION = 120.0 #float(sys.argv[4])  # In seconds, or -(port#) if negative.


# Create a process-shared table keyed on timestamps
# and holding references to allocated image memory.
images = multiprocessing.Manager().dict()
lastpan = 0
lasttilt = 0
camwaittime = datetime.datetime.now()
avcount = 0
avx = 0
avy = 0
class Detector(mpipe.OrderedWorker):
    """Detects objects."""
    def __init__(self, classifier, color):
        self._classifier = classifier
        self._color = color

    def doTask(self, tstamp):
        """Run object detection."""
        result = list()
        try:
            image = images[tstamp]

            height, width = image.shape[:2]
            gray = cv2.resize(
            image,
            (int(width/3), int(height/3))
            )
            gray = cv2.cvtColor(
            gray,
            cv2.COLOR_BGR2GRAY
            )
            gray = cv2.equalizeHist(
            gray
            )


            #size = np.shape(image)[:2]
            rects = self._classifier.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=3,
                minSize=(20,20),
                flags=cv2.cv.CV_HAAR_FIND_BIGGEST_OBJECT | cv2.cv.CV_HAAR_DO_CANNY_PRUNING | cv2.cv.CV_HAAR_DO_ROUGH_SEARCH

                )
            if len(rects):
                for a,b,c,d in rects:
                    result.append((a,b,c,d, self._color))
        except:
            print('Error in detector !!!')
        return result

# Monitor framerates for the given seconds past.
framerate = coils.RateTicker((2,))

class Postprocessor(mpipe.OrderedWorker):
    def doTask(self, (tstamp, rects,)):
        first = True
        """Augment the input image with results of processing."""
        size = np.shape(images[tstamp])[:2]
        # Make a flat list from a list of lists .
        rects = [item for sublist in rects for item in sublist]

        # Draw rectangles.
        for x1, y1, x2, y2, color in rects:
            x1 *= 3
            y1 *= 3
            x2 *= 3
            y2 *= 3
            cv2.rectangle(
                images[tstamp],
                (x1, y1), (x1+x2, y1+y2),
                color=color,
                thickness=2,
                )
            if first == True:
                global lastpan
                global lasttilt
                global camwaittime
                global avcount
                global avx
                global avy
                now = datetime.datetime.now()
                if camwaittime < now:

                    #Find face center
                    x = float(x1 + (x2 / 2))
                    y = float(y1 + (y2 / 2))
                    first = False
                    #print(x, y, 'face center', size)
                    ixc = float((size[1] / 2))
                    iwc = float((size[0] / 2))
                    #print(ixc, iwc, 'image center')
                    offsetx = float(((ixc - x) / ixc))
                    offsety = float(((y - iwc) / iwc))
                    #print(offsetx, offsety, 'percent off center')
                    #print(lastpan, lasttilt)
                
                    
                    aovx = (offsetx * 27.0)
                    aovy = (offsety * 20.5)
                    if avcount < 10:
                        avcount += 1
                        avx += aovx
                        avy += aovy
                    else:
                        avox = avx / 10
                        avoy = avy / 10
                        print(aovx, aovy, 'Angle of view')
                        if abs(aovx) > abs(aovy):
                            camwaitsecs = ((abs(aovx) / 90) * 6)
                        else:
                            camwaitsecs = ((abs(aovy) / 90) * 6)
                        print(camwaitsecs, 'Cam wait secs')
                        camwaittime = now + datetime.timedelta(seconds=abs(camwaitsecs))
                        nextpan = int(lastpan + aovx)
                        nexttilt = int(lasttilt + aovy)
                        #print(nextpan, nexttilt)
                        pan(nextpan)
                        tilt(nexttilt)
                        lastpan = nextpan
                        lasttilt = nexttilt
                        avcount = 0
        # Write image dimensions and framerate.

        fps_text = '{:.2f} fps'.format(*framerate.tick())
        util.writeOSD(
            images[tstamp],
            ('{0}x{1}'.format(size[1], size[0]), fps_text),
            )

        return tstamp

root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
startx = (screen_width/2) - (WIDTH/2)
starty = (screen_height/2) - (HEIGHT/2)
#Center window in screen
cv2.namedWindow('object detection 3')
cv2.moveWindow('object detection 3', startx, starty)
#Default start position
pan(0)
tilt(-40)
lastpan = 0
lasttilt = -40

class Viewer(mpipe.OrderedWorker):
    """Displays image in a window."""
    def doTask(self, tstamp):
        try:
            image = images[tstamp]
            cv2.imshow('object detection 3', image)
            cv2.waitKey(1)
        except:
            print('Error in viewer !!!')
        return tstamp

# Create the detector stages.
detector_stages = list()
for classi in util.cascade.classifiers:
    detector_stages.append(
        mpipe.Stage(
            Detector, 1, 
            classifier=classi, 
            color=util.cascade.colors[classi]),
        )

# Assemble the image processing pipeline:
#
#   detector(s)                      viewer
#     ||                               ||
#   filter_detector --> postproc --> filter_viewer
#
filter_detector = mpipe.FilterStage(
    detector_stages,
    max_tasks=1,
    cache_results=True,
    )
postproc = mpipe.Stage(Postprocessor)
filter_viewer = mpipe.FilterStage(
    (mpipe.Stage(Viewer),), 
    max_tasks=2,
    drop_results=True,
    )

filter_detector.link(postproc)
postproc.link(filter_viewer)
pipe_iproc = mpipe.Pipeline(filter_detector)

# Create an auxiliary process (modeled as a one-task pipeline)
# that simply pulls results from the image processing pipeline, 
# and deallocates associated shared memory after allowing
# the designated amount of time to pass.
def deallocate(tdelta):
    for tstamp in pipe_iproc.results():
        elapsed = datetime.datetime.now() - tstamp
        if tdelta - elapsed > datetime.timedelta():
            time.sleep(tdelta.total_seconds())
        del images[tstamp]
pipe_dealloc = mpipe.Pipeline(mpipe.UnorderedStage(deallocate))
pipe_dealloc.put(datetime.timedelta(microseconds=1e6))  # Start it up right away.

# Create the OpenCV video capture object.
cap = cv2.VideoCapture(DEVICE)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)
time.sleep(2)
# Run the video capture loop, allocating shared memory
# and feeding the image processing pipeline.
# Run for configured duration, or (if duration < 0) until we
# connect to socket (duration re-interpreted as port number.)
now = datetime.datetime.now()
end = now + datetime.timedelta(seconds=abs(DURATION))
while end > now or DURATION < 0:

    if DURATION < 0:
        # Bail if we connect to socket.
        try:
            socket.socket().connect(('', int(abs(DURATION))))
            print('stopping')
            break
        except:
            pass
                  
    # Mark the timestamp. This is the index by which 
    # image procesing stages will access allocated memory.
    now = datetime.datetime.now()

    # Capture the image.
    hello, image = cap.read()
    image = cv2.flip(image, -1)
    

    # Allocate shared memory for a copy of the input image.
    shape = np.shape(image)
    dtype = image.dtype
    image_in = sharedmem.empty(shape, dtype)

    # Copy the input image to its shared memory version.
    image_in[:] = image.copy()
    
    # Add to the images table.
    images[now] = image_in  # Input image.

    # Put the timestamp on the image processing pipeline.
    pipe_iproc.put(now)

# Signal pipelines to stop, and wait for deallocator
# to free all memory.
pipe_iproc.put(None)
pipe_dealloc.put(None)
for result in pipe_dealloc.results():
    pass

# The end.
