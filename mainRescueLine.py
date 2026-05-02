##################################################################################
# Imports
##################################################################################

import cv2
import numpy as np
from picamera2 import Picamera2
from greenSquareDetection import organizeGreenSquarePoints, computeCentroids, findFwdAngle, findGreenSquareLines, updateStateOnGreenSquares
from searchForDestinationPoint import determineDestinationPoint, findOldPos, collectOuterIntervals
from navigation import moveToDestinationPoint, findRobotPos, handleLostLine
from ledRing import turnLedOn, turnLedOff
from newMotors import stopRobot
from popup import Popup
from utilities import drawCandidatePoints, getBinaryFrame, captureFrame, calcAngleWithHorizontal

##################################################################################
# Initialization
##################################################################################

### Camera ###
picam = Picamera2()
config = picam.create_preview_configuration(main={"format":"RGB888"})
picam.start()

### Initialize GUI ###
calibrationGUI = Popup()
calibrationGUI.createButtons()
calibrationGUI.createRGBLabels()

##################################################################################
# Variables
##################################################################################

warnings = []

lower_black = (0,0,0)
upper_black = (180,225,130)
lower_green = np.array([35, 60, 60])
upper_green = np.array([85, 255, 255])

### Initialize variables for line following ###
prev_desired_pos = None
frame = picam.capture_array()
height, width = frame.shape[:2]
old_pos = (width//2,height-1)
base_speed = 35
line_follow_threshold = 600

# place robot on the image at the middle of the line
robot_pos = (int(width/2), int(height/2))

# memory
prev_destination_angle = None
line_follow_state = "normal"

##################################################################################
# Calibration
##################################################################################

# close the window when x is clicked
def on_close():
    calibrationGUI.window.destroy()

def previewActions():
    # pass in new r,g,b values to led ring
    turnLedOn(calibrationGUI.red, calibrationGUI.green, calibrationGUI.blue)
    cv2.imshow("Preview", picam.capture_array())
    # schedule the function to run again in 30 ms
    cv2.waitKey(1)
    calibrationGUI.window.after(30, previewActions)
    
calibrationGUI.window.protocol("WM_DELETE_WINDOW", on_close)
previewActions()
calibrationGUI.display_window()

# cleanup work for when the user quits out of the program or kills the program
def cleanup():
    picam.stop()
    turnLedOff()
    stopRobot()
    cv2.destroyAllWindows()

##################################################################################
# Line follow
##################################################################################

try:
    while True:
        print("******************WARNINGS: ",warnings)

        ### Get images from camera ###
        frame, hsv = captureFrame(picam)
        frame_binary, black_pixels = getBinaryFrame(hsv, lower_black, upper_black)

        # Create green square mask
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.GaussianBlur(mask, (5,5), 0)

        non_zero_pixels = cv2.findNonZero(mask)
        destination_pxl = None
        greenPresent = True if non_zero_pixels is not None else False
        
        # handle overshoot on black line turning
        if line_follow_state == "normal" and black_pixels is None or len(black_pixels) < line_follow_threshold:
            handleLostLine(base_speed, frame_binary, width, height, 0 if black_pixels is None else len(black_pixels), line_follow_threshold)
            continue

        # get intervals + old pos
        robot_pos = findRobotPos(black_pixels)
        intervals = collectOuterIntervals(frame_binary, width, height, greenPresent)
        old_pos, intervals = findOldPos(intervals, old_pos)

        if greenPresent:
            square_groups = organizeGreenSquarePoints(mask, non_zero_pixels, frame, height, width)
            edges = cv2.Canny(mask, 100,200)
            green_square_lines = findGreenSquareLines(frame, edges)
            fwd_angle = findFwdAngle(green_square_lines, height, width, old_pos[0])
            centroids = computeCentroids(square_groups, frame)
            line_follow_state = updateStateOnGreenSquares(centroids, fwd_angle, mask, width, height, frame, line_follow_state)
            cv2.imshow("edges", edges)
        if line_follow_state == "normal":
            # Draw the line that represents which way the robot came from (old pos --> current robot pos)
            cv2.line(frame, old_pos, robot_pos, (255,0,0), 10)

            # Old orientation is the angle between the line from the old robot pos to the curr robot pos and the horizontal, measured counterclockwise from the horizontal. 
            old_orientation = calcAngleWithHorizontal(old_pos, robot_pos)

            # Each average pixel is a candidate for the destination point of the robot. 
            # The one with the angle closest to the old orientation should be considered the destination point
            candidates = []
            for interval in intervals:
                candidates.append((interval.midpoint_x, interval.midpoint_y))

            cv2.circle(frame, old_pos, 20, (255,0,), -1)
            drawCandidatePoints(frame, candidates)
            destination_pxl, destination_angle = determineDestinationPoint(candidates, robot_pos, old_orientation, frame, old_pos)

            if destination_pxl is None:
                handleLostLine(base_speed, frame_binary, width, height, 0 if black_pixels is None else len(black_pixels), line_follow_threshold)
                continue
        elif line_follow_state == "green-square-turnleft":
            pass
        elif line_follow_state == "green-square-turnright":
            pass
        elif line_follow_state == "U-turn":
            pass
                
        ### Drawings ###
        cv2.circle(frame, robot_pos, 18, (0,255,0), -1) # Draw robot
        cv2.circle(frame, destination_pxl, 18, (255,102,255), -1) # Draw destination
        
        ### Showing frames after calculations ###
        cv2.imshow("Binary mask", frame_binary) # frame with line isoalted
        cv2.imshow("mask", mask) # Green square mask
        cv2.imshow("Robot Map", frame) # Original frame but with calculations

        line_follow_state = moveToDestinationPoint(destination_angle, prev_destination_angle, base_speed, width//2, robot_pos[0])
        prev_destination_angle = destination_angle
        if cv2.waitKey(1) == ord('q'):
            break
except KeyboardInterrupt:
    cleanup()
finally:
    cleanup()