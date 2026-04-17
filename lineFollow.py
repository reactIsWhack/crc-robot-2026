import cv2
import numpy as np
from picamera2 import Picamera2
import math
import time
from greenSquareDetection import organizeGreenSquarePoints, computeCentroids, findLineDirection, checkFwdForBlack, checkBwdForBlack
from searchForDestinationPoint import searchRows, searchCols, calcAngleWithHorizontal, determineDestinationPoint, searchBeen, findOldPos, moveToDestinationPoint 
from ledRing import turnLedOn, turnLedOff
from newMotors import stopRobot
from popup import Popup

picam = Picamera2()
config = picam.create_preview_configuration(main={"format":"RGB888"})
picam.start()

ledPopup = Popup()
ledPopup.createButtons()
ledPopup.createRGBLabels()
prev_desired_pos = None
frame = picam.capture_array().copy()
h,w = frame.shape[:2]
old_pos = (w//2,0)

def followLine():
    try:
        turnLedOn(ledPopup.red, ledPopup.green, ledPopup.blue)
        global prev_desired_pos
        global old_pos

        frame = picam.capture_array() # video frame in bgr format
        frame_copy = frame.copy()
        frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGB2BGR)

        frame_copy = cv2.GaussianBlur(frame_copy, (5, 5), 0)
        hsv = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2HSV) 


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
        
        if old_pos is None or len(avg_pxls_bottom) == 0:
            return
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
        destination_pxl, destination_angle = determineDestinationPoint(avg_pixels, robot_pos, robot_orientation, frame_copy, old_pos)

        # if there is a large change in the x or y coordiante of the desired position, stop the robot so it can readjust its alignment
        max_change = 10

        if destination_pxl is None:
            print("no destination pixel found")
            return

        if prev_desired_pos is not None and abs(destination_pxl[0]-prev_desired_pos[0]) >= max_change and abs(destination_pxl[1]-prev_desired_pos[1]) >= max_change:
            stopRobot()
            pass
        
        cv2.circle(frame_copy, destination_pxl, 18, (255,102,255), -1)
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
        moveToDestinationPoint(destination_angle)

        prev_desired_pos = destination_pxl
        if cv2.waitKey(1) == ord('q'):
            on_close()
    finally:
        ledPopup.window.after(30, followLine)

def on_close():
    picam.stop()
    turnLedOff()
    cv2.destroyAllWindows()
    ledPopup.window.destroy()
    stopRobot()

ledPopup.window.protocol("WM_DELETE_WINDOW", on_close)
followLine()
ledPopup.display_window()