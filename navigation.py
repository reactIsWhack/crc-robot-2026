from newMotors import moveFR, moveFL, moveBL, moveBR, moveRobotLeft, moveRobotRight, moveRobotFwdOrBwd
from utilities import checkInRange
from searchForDestinationPoint import collectOuterIntervals

def moveToDestinationPoint(destination_angle, prev_destination_angle, base_speed, camera_x, line_x):
    turn_error = 10

    # check if the robot needs to turn
    if not checkInRange(90-turn_error, 90+turn_error, destination_angle):
        direction = 'right' if destination_angle < 90 or destination_angle > 270 else 'left'
        if direction == 'right':
            moveRobotRight(base_speed)
        else:
            moveRobotLeft(base_speed)
    else:
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
