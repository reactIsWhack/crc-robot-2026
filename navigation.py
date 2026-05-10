from newMotors import moveFR, moveFL, stopRobot, moveBL, moveBR, moveRobotLeft, moveRobotRight, moveRobotFwdOrBwd
from tools.utilities import checkInRange, calcAngleWithHorizontal, getCandidates
from searchForDestinationPoint import collectOuterIntervals, findOldPos, determineDestinationPoint
import time
import cv2

def moveToDestinationPoint(destination_angle, line_follow_state, base_speed, line_x, old_pos_data):
    turn_error = 25
    green_square_turn = line_follow_state == "green-square-turnleft" or line_follow_state == "green-square-turnright"
    old_pos, w, h = old_pos_data
    camera_x = w//2

    # check if the robot needs to turn
    if not checkInRange(90-turn_error, 90+turn_error, destination_angle):
        if not green_square_turn:
            line_follow_state = "regular-turn"
        
        direction = 'right' if destination_angle < 90 or destination_angle > 270 else 'left'
        if direction == 'right':
            moveRobotRight(base_speed)
        else:
            moveRobotLeft(base_speed)
    else:
        line_follow_state = "normal"
        correctLineFollowing(camera_x, line_x, base_speed)    
        old_pos = (w//2,h-1)    
    
    return line_follow_state, old_pos

def correctLineFollowing(camera_x, line_x, base_speed):
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
    left_motors = min(max(0, left_motors), 100)
    right_motors = min(max(0, right_motors), 100)
    return (left_motors, right_motors)
        
# the robot pos will be the center of the line (centroid)
def findRobotPos(black_pixels):
    x_sum = 0
    y_sum = 0
    total_black_pixels = len(black_pixels)
    for i in range(total_black_pixels):
        x_sum += black_pixels[i][0][0]
        y_sum += black_pixels[i][0][1]
    centroid_x = x_sum//total_black_pixels
    centroid_y = y_sum//total_black_pixels
    return (centroid_x, centroid_y)

def handleLostLine(base_speed, frame_binary, width, height, total_black_pixels, line_follow_threshold):
    if len(collectOuterIntervals(frame_binary, width, height)) < 2 and total_black_pixels < line_follow_threshold:
        moveRobotFwdOrBwd(base_speed, "bwd")

def makeUTurn(initial_uturn_complete, w, h, frame_binary, black_pixels, frame): # return = (old pos, state, initial_uturn_complete)
    old_pos = (w//2, h-1) # default old pos to middle of bottom row
    if not initial_uturn_complete:
        moveRobotRight(60) # speed = 60
        time.sleep(3) # replace with time needed for a 150 deg turn
        stopRobot()
        return (old_pos, "U-turn", True)

    intervals = collectOuterIntervals(frame_binary, w, h)
    total_screen_pixels = w * h
    if intervals is not None and len(intervals) >= 2 and len(black_pixels) >= 0.2*total_screen_pixels:
        lineCenter = findRobotPos(black_pixels)
        old_pos, _ = findOldPos(intervals, old_pos)
        candidates = getCandidates(intervals)
        orientationAngle = calcAngleWithHorizontal(old_pos, lineCenter)
        destination_pxl = determineDestinationPoint(candidates, lineCenter, orientationAngle, old_pos)
        destination_angle = calcAngleWithHorizontal(lineCenter, destination_pxl)
        
        
        target_orientation = 90
        error = 20
        cv2.line(frame, old_pos, lineCenter, (255,0,0), 10) # orientation line
        cv2.line(frame, lineCenter, destination_pxl, (0,0,255), 10) # destination line
        cv2.imshow("U-turn Frame", frame)
        print(f"orientation angle={orientationAngle}, destination angle = {destination_angle}")
        if checkInRange(target_orientation-error, target_orientation+error, orientationAngle):
            stopRobot()
            return (old_pos, "normal", False)

    moveRobotRight(35)
    return (old_pos, "U-turn", True) # default old pos = (w//2, h-1)

