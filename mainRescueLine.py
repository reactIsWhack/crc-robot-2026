##################################################################################
# Imports
##################################################################################

import cv2
import numpy as np
from picamera2 import Picamera2
from greenSquareDetection import computeCentroids, findFwdAngle, findGreenSquareLines, updateStateOnGreenSquares, exploreImageBorderClockwise, exploreImageBorderCounterClockwise
from searchForDestinationPoint import determineDestinationPoint, findOldPos, collectOuterIntervals
from navigation import moveToDestinationPoint, findRobotPos, makeUTurn, moveRobotFwdOrBwd, flipOldPosAndDestination, stopAtRedLine, handleNoDestination, handleTurnLostLine
from tools.ledRing import turnLedOn, turnLedOff
from newMotors import stopRobot
from tools.popup import Popup
from tools.utilities import drawCandidatePoints, captureFrame, calcAngleWithHorizontal, createOneIndexedBorder, renderRobotMap, drawOnRobotMap, getCandidates, renderBinaryFrame
from createBlackLineMask import createMask
from time import sleep
from obstacleDetection import detectObstacle

##################################################################################
# Initialization
##################################################################################

### Camera ###
picam = Picamera2()
config = picam.create_preview_configuration(main={"format":"BGR888", "size":(640,480)})
picam.start(config)

### Initialize GUI ###
calibrationGUI = Popup()
calibrationGUI.createButtons()
calibrationGUI.createRGBLabels()
monitor_width = 800
monitor_height = 480

##################################################################################
# Variables
##################################################################################
lower_black = (0,0,0)
upper_black = (180,225,65)
lower_green = np.array([35, 60, 60])
upper_green = np.array([85, 255, 255])

### Initialize variables for line following ###
frame = picam.capture_array()
height, width = frame.shape[:2]
image_border = createOneIndexedBorder(width, height)
old_pos = (width//2,height-1)
base_speed = 35
line_follow_threshold = 600
orientation_error = 10

# place robot on the image at the middle of the line
robot_pos = (int(width/2), int(height/2))

# memory
line_follow_state = "regular-turn"
initial_uturn_complete = False
uturn_stepfwd = False
turnDir = ""
recoverCounter = 0

##################################################################################
# Calibration
##################################################################################

# close the window when x is clicked
def on_close():
    calibrationGUI.window.destroy()
    cv2.destroyAllWindows()

def previewActions():
    cv2.namedWindow("Preview", cv2.WINDOW_NORMAL)
    cv2.moveWindow("Preview", monitor_width-width+200, 0)
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
sleep(1)
consecutive_red = 0

try:
    while True:
        if consecutive_red == 100:
            quit()
        
        print(f"line follow state = {line_follow_state}")
        ### Get images from camera ###
        frame, hsv = captureFrame(picam)
        frame_binary, black_pixels = createMask(width, height, hsv, frame)
        consecutive_red = stopAtRedLine(hsv, consecutive_red)

        if consecutive_red > 0:
            continue

        if line_follow_state == "turn-lost-line":
            line_follow_state, recoverCounter, turnDir = handleTurnLostLine(frame_binary, width, height, line_follow_state, turnDir, base_speed, recoverCounter)
            renderRobotMap(frame, "Robot Map Regular")
            renderBinaryFrame(frame_binary, "Frame Binary")
            continue
        
        # Create green square mask
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.GaussianBlur(mask, (5,5), 0)
        non_zero_pixels = cv2.findNonZero(mask)
        greenPresent = True if non_zero_pixels is not None else False
        renderBinaryFrame(frame_binary, "frame binary")

        if line_follow_state == "U-turn":
            if len(black_pixels) > 0.1*(width*height) and uturn_stepfwd:
                moveRobotFwdOrBwd(base_speed, "fwd")
            else:
                uturn_stepfwd = False
                old_pos, line_follow_state, initial_uturn_complete = makeUTurn(initial_uturn_complete, width, height, frame_binary, black_pixels, frame)
                renderRobotMap(frame, "Robot Map Regular")
                cv2.waitKey(1)
            continue

        destination_pxl = destination_angle = None
        green_square_states = {}
        approaching_green = False

        # get intervals + old pos
        intervals = collectOuterIntervals(frame_binary, width, height, line_follow_state, image_border)
        old_pos, intervals = findOldPos(intervals, old_pos, width, height) # the new intervals array is the same as the original one, except the interval containing old pos is removed
        cv2.circle(frame, old_pos, 10, (255,0,0), -1)

        if line_follow_state == "gap":
            if len(intervals) == 0:                
                moveRobotFwdOrBwd(base_speed, "fwd")
                renderRobotMap(frame, "Robot Map Regular")
                continue
            else:
                line_follow_state = "normal"
        
        robot_pos = findRobotPos(black_pixels, width, height)
        old_pos_idx = image_border.index(old_pos)

        # Old orientation is the angle between the line from the old robot pos to the curr robot pos and the horizontal, measured counterclockwise from the horizontal. 
        old_orientation = calcAngleWithHorizontal(old_pos, robot_pos)

        # Each average pixel is a candidate for the destination point of the robot. 
        # The one with the angle closest to the old orientation should be considered the destination point
        candidates = getCandidates(intervals)

        if greenPresent and line_follow_state != "U-turn":
            edges = cv2.Canny(mask, 100,200)
            green_square_lines = findGreenSquareLines(frame, edges)
            if len(green_square_lines) != 0:
                centroids = computeCentroids(mask)
                fwd_angle = findFwdAngle(green_square_lines, height, width, old_pos[0])
                green_square_states, line_follow_state = updateStateOnGreenSquares(centroids, fwd_angle, frame_binary, width, height, frame, line_follow_state, mask)
                print(f"line follow state after green square analysis: {line_follow_state}")
            approaching_green = line_follow_state == "normal" or line_follow_state == "regular-turn"
        if line_follow_state == "normal" or line_follow_state == "regular-turn":
            drawCandidatePoints(frame, candidates)
            destination_pxl = determineDestinationPoint(candidates, robot_pos, old_orientation, old_pos)
        elif line_follow_state == "green-square-turnleft":
            destination_pxl = exploreImageBorderClockwise(old_pos_idx, candidates, image_border)
        elif line_follow_state == "green-square-turnright":
            destination_pxl = exploreImageBorderCounterClockwise(old_pos_idx, candidates, image_border)
        elif line_follow_state == "U-turn":
            uturn_stepfwd = True
            continue
        elif line_follow_state == "obstacle":
            pass

        if destination_pxl is None:
            line_follow_state = handleNoDestination(line_follow_state, old_orientation)
            renderRobotMap(frame, "Robot Map Regular")
            continue
        old_pos, destination = flipOldPosAndDestination(old_pos, destination_pxl)

        destination_angle = calcAngleWithHorizontal((width//2, height//2), destination_pxl) if destination_pxl is not None else None
        ### Drawings ###
        drawOnRobotMap(frame, robot_pos, destination_pxl, old_pos)

        ### Showing frames after calculations ###
        renderRobotMap(frame, "Robot Map Regular")

        new_base_speed = 15 if approaching_green else base_speed
        line_follow_state, old_pos, turnDir = moveToDestinationPoint(destination_angle, line_follow_state, new_base_speed, robot_pos[0], (old_pos, width, height))

        if cv2.waitKey(1) == ord('q'):
            break
except KeyboardInterrupt:
    cleanup()
finally:
    cleanup()