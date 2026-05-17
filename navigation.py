from newMotors import moveFR, moveFL, stopRobot, moveBL, moveBR, moveRobotLeft, moveRobotRight, moveRobotFwdOrBwd
from tools.utilities import checkInRange, calcAngleWithHorizontal, getCandidates
from searchForDestinationPoint import collectOuterIntervals, printIntervals,findOldPos, determineDestinationPoint
import time
import cv2
import numpy as np

def moveToDestinationPoint(destination_angle, line_follow_state, base_speed, line_x, old_pos_data):
    turn_error = 30
    green_square_turn = line_follow_state == "green-square-turnleft" or line_follow_state == "green-square-turnright"
    old_pos, w, h = old_pos_data
    camera_x = w//2
    turn_dir = "fwd"

    # check if the robot needs to turn
    if not checkInRange(90-turn_error, 90+turn_error, destination_angle):
        direction = 'right' if destination_angle < 90 or destination_angle > 270 else 'left'
        turn_dir = direction
        
        if not green_square_turn:
            line_follow_state = "regular-turn"
            base_speed = base_speed + 15
        else:
            base_speed = base_speed - 5

        if direction == 'right':
            moveRobotRight(base_speed)
        else:
            moveRobotLeft(base_speed)
    else:
        if not green_square_turn:
            line_follow_state = "normal"
        print("MOVING FWD")
        moveRobot(camera_x, line_x, base_speed)    
        old_pos = (w//2,h-1)    
    
    return line_follow_state, old_pos, turn_dir

def moveRobot(camera_x, line_x, base_speed):
    left_speed, right_speed = calcMotorSpeeds(camera_x, line_x, base_speed)
    moveFR(right_speed, "fwd")
    moveBR(right_speed, "fwd")
    moveFL(left_speed, "fwd")
    moveBL(left_speed, "fwd")

def calcMotorSpeeds(camera_x, line_x, base_speed):
    # magnitude of error represents distance b/w camera and the line's center. 
    # Negative error means line is to the left of the camera, positive error means line is to the right of the camera.
    error = line_x - camera_x
    kp = 0.08
    turn = kp * error

    left_motors = base_speed + turn
    right_motors = base_speed - turn

    # clamp left_motors and right_motors to be in the range [0, 100] for duty cycle
    left_motors = min(max(0, left_motors), 65)
    right_motors = min(max(0, right_motors), 65)
    return (left_motors, right_motors)

# the robot pos will be the center of the line (centroid)
def findRobotPos(black_pixels, w, h):
    x_sum = 0
    y_sum = 0
    total_black_pixels = len(black_pixels)
    for i in range(total_black_pixels):
        x_sum += black_pixels[i][0][0]
        y_sum += black_pixels[i][0][1]

    if total_black_pixels == 0:
        return (w//2, h//2)
    centroid_x = x_sum//total_black_pixels
    centroid_y = y_sum//total_black_pixels
    return (centroid_x, centroid_y)

def makeUTurn(initial_uturn_complete, w, h, frame_binary, black_pixels, frame): # return = (old pos, state, initial_uturn_complete)
    old_pos = (w//2, h-1) # default old pos to middle of bottom row
    if not initial_uturn_complete:
        moveRobotRight(60) # speed = 60
        time.sleep(3) # replace with time needed for a 150 deg turn
        stopRobot()
        return (old_pos, "U-turn", True)

    intervals = collectOuterIntervals(frame_binary, w, h, "U-turn", [])
    total_screen_pixels = w * h
    if intervals is not None and len(intervals) >= 2 and len(black_pixels) >= 0.2*total_screen_pixels:
        lineCenter = findRobotPos(black_pixels, w, h)
        old_pos, _ = findOldPos(intervals, old_pos, w, h)
        candidates = getCandidates(intervals)
        orientationAngle = calcAngleWithHorizontal(old_pos, lineCenter)
        destination_pxl = determineDestinationPoint(candidates, lineCenter, orientationAngle, old_pos)
        destination_angle = calcAngleWithHorizontal(lineCenter, destination_pxl)
        
        
        target_orientation = 90
        error = 20
        cv2.line(frame, old_pos, lineCenter, (255,0,0), 10) # orientation line
        cv2.line(frame, lineCenter, destination_pxl, (0,0,255), 10) # destination line
        # cv2.imshow("U-turn Frame", frame)
        print(f"orientation angle={orientationAngle}, destination angle = {destination_angle}")
        if checkInRange(target_orientation-error, target_orientation+error, orientationAngle):
            stopRobot()
            return (old_pos, "normal", False)

    moveRobotRight(35)
    return (old_pos, "U-turn", True) # default old pos = (w//2, h-1)

def flipOldPosAndDestination(old_pos, destination):
    if old_pos[1] < destination[1]:
        temp = old_pos
        old_pos = destination
        destination = temp
    return old_pos, destination

def stopAtRedLine(hsv, consecutive_red):
    lower_red1 = np.array([0, 160, 125])
    upper_red1 = np.array([3, 255, 195])    
    lower_red2 = np.array([177, 160, 125])
    upper_red2 = np.array([179, 255, 195])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    red_mask = mask1 | mask2
    non_zero_pixels_red = cv2.findNonZero(red_mask)
    if non_zero_pixels_red is not None:
        stopRobot()
        consecutive_red += 1
    else:
        consecutive_red = 0
    return consecutive_red

def handleNoDestination(line_follow_state, robot_orientation):
    gap_error = 10
    if checkInRange(90-gap_error, 90+gap_error, robot_orientation) or line_follow_state == "gap":
        line_follow_state = "gap"
    elif line_follow_state == "regular-turn" or line_follow_state == "normal":
        line_follow_state = "turn-lost-line"
    return line_follow_state


def handleTurnLostLine(frame_binary, w, h, line_follow_state, turnDir, base_speed, counter):
    intervals = collectOuterIntervals(frame_binary, w, h, line_follow_state, [])
    if counter == 50:
        turnDir = "right" if turnDir == "left" else "left"

    print(f"RECOVER COUNTER={counter}, TURN DIR={turnDir}")
    if len(intervals) >= 2:
        line_follow_state = "normal"
        counter = 0
        print(f"intervals = {printIntervals(intervals)}")
    else:
        counter += 1
        if turnDir == "left":
            print("TURNING LEFT")
            moveRobotLeft(base_speed)
        else:
            print("TURNING RIGHT")
            moveRobotRight(base_speed)
    return line_follow_state, counter, turnDir