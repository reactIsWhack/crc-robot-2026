import cv2
import numpy as np
from picamera2 import Picamera2
import math
import time
from greenSquareDetection import organizeGreenSquarePoints, computeCentroids, findLineDirection, checkFwdForBlack, checkBwdForBlack
from searchForDestinationPoint import searchRows, searchCols, calcAngleWithHorizontal, determineDestinationPoint, searchBeen, findOldPos
from ledRing import turnLedOn, turnLedOff

picam = Picamera2()
config = picam.create_preview_configuration(main={"format":"RGB888"})
picam.start()
picam.set_controls({
    "AeEnable":False,
    "ExposureTime":10000,
    "AnalogueGain":1.0,
    "AwbEnable":False,
    "ColourGains":(1.6,1.6)
})

frame = picam.capture_array().copy()
h,w = frame.shape[:2]
old_pos = (w//2,0)
turnLedOn()

try:
    while True:
        frame = picam.capture_array() # video frame in bgr format
        frame_copy = frame.copy()

        frame_copy = cv2.GaussianBlur(frame_copy, (5, 5), 0)
        hsv = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2HSV) 
        print(f"Dimensions: height={frame_copy.shape[0]}, width={frame_copy.shape[1]}")

        lower_black = (0,0,0)
        upper_black = (180,225,130)
        mask_for_black = cv2.inRange(hsv, lower_black, upper_black)
        frame_bin = cv2.bitwise_not(mask_for_black)
        height, width = frame_bin.shape
        cv2.imshow("Camera Capture", frame_copy)
        cv2.imshow("Frame Bin", frame_bin)

        # search top and bottom rows for edge pixels
        avg_pxls_top = searchRows(frame_bin, 0, width, frame_copy)
        avg_pxls_bottom = searchRows(frame_bin, height-1, width, frame_copy)

        # # search left and right rows for edge pixels
        avg_pxls_left = searchCols(frame_bin, 0, height, frame_copy)
        avg_pxls_right = searchCols(frame_bin, width - 1, height, frame_copy)
        
        if old_pos == None or len(avg_pxls_bottom) == 0:
            continue
        old_pos = findOldPos(old_pos[0], avg_pxls_bottom, frame_copy)
        # place robot on the image at the middle of the line
        robot_pos = (int(width/2), int(height/2))
        cv2.circle(frame_copy, robot_pos, 18, (0,255,0), -1)

        cv2.line(frame_copy, old_pos, robot_pos, (255,0,0), 10)
        # robot orientation is the angle between the line from the old robot pos to the curr robot pos and the horizontal, measured counterclockwise from the horizontal. 
        robot_orientation = calcAngleWithHorizontal(old_pos, robot_pos, frame_copy)
        cv2.putText(frame_copy, str(robot_orientation)[0:6]+" deg", (robot_pos[0]+20, robot_pos[1]+70), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (128,0,128), 5, cv2.LINE_AA)

        # each average pixel is a candidate for the destination point of the robot. 
        # The one with the angle closest to the robot orientation should be considered the destination point
        avg_pixels = []
        avg_pixels.extend(avg_pxls_left)
        avg_pixels.extend(avg_pxls_right)
        avg_pixels.extend(avg_pxls_top)
        avg_pixels.extend(avg_pxls_bottom)
        destination_pxl = determineDestinationPoint(avg_pixels, robot_pos, robot_orientation, frame_copy, old_pos)
        cv2.circle(frame_copy, destination_pxl, 18, (255,102,255), -1)

        if destination_pxl == None:
            continue

        # create mask
        lower_green = np.array([35, 60, 60])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.GaussianBlur(mask, (7,7), 0)

        non_zero_pixels = cv2.findNonZero(mask)
        greenPresent = True if non_zero_pixels is not None else False
        if greenPresent:
            square_groups = organizeGreenSquarePoints(mask, non_zero_pixels, frame_copy, height, width)
            centroids = computeCentroids(square_groups, frame_copy)
            lineDirection = findLineDirection(old_pos, destination_pxl, frame_copy, robot_pos)
            checkFwdForBlack(frame_copy, lineDirection, frame_bin, height, width, centroids)
            checkBwdForBlack(frame_copy, lineDirection, frame_bin, height, width, centroids)

        #lastBack = searchBeen(frame_bin, lastBack, height-1, width)
        # cv2.circle(frame_copy, (lastBack,height-1), 36, (255,0,255), -1)

        cv2.imshow("Robot Map", frame_copy)
        cv2.imshow("mask", mask)
        print("alive")


        if cv2.waitKey(1) == ord('q'):
            break
        time.sleep(0.75)
finally:
    picam.stop()
    turnLedOff()
    cv2.destroyAllWindows()