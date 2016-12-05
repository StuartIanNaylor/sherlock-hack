"""Image processing routines."""

import datetime
import cv2
import numpy as np
    

def writeOSD(image, lines, size=0.02):
    """Write text given in *lines* iterable, 
    the height of each line determined by *size* as
    proportion of image height."""

    # Compute row height at scale 1.0 first.
    (letter_width, letter_height), baseline = cv2.getTextSize(
        text='I', 
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1.0,
        thickness=1)

    # Compute actual scale to match desired height. 
    image_height = np.shape(image)[0]
    line_height = int(image_height * size)
    scale = float(line_height) / letter_height

    # Deterimine base thickness, based on scale.
    thickness = int(scale * 4)

    # Increase line height, to account for thickness.
    line_height += thickness * 3

    # Iterate the lines of text, and draw them.
    xoffset = int(letter_width * scale)
    yoffset = line_height
    for line in lines:
        cv2.putText(  # Draw the drop shadow.
            image,
            text=line,
            org=(xoffset+max(1, thickness/2), yoffset+max(1, thickness/2)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=scale,
            color=(0, 0, 0),
            thickness=thickness,
            )
        cv2.putText(  # Draw the text body.
            image,
            text=line,
            org=(xoffset, yoffset),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=scale,
            color=(215, 215, 70),
            thickness=thickness,
            )
        cv2.putText(  # Draw the highlight.
            image,
            text=line,
            org=(xoffset-max(1, thickness/3), yoffset-max(1, thickness/3)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=scale,
            color=(245, 255, 200),
            thickness=thickness/3,
            )
        yoffset += line_height
        
# The end.
