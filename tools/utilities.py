from time import sleep
import math
import cv2

def checkInRange(lower, upper, value):
    return value >= lower and value <= upper

def calcEuclidianDist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def captureFrame(picam):
    frame = picam.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # convert from RGB to BGR for opencv functions to work properly

    # Transformations
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # obtain hsv image for masking
    return frame, hsv

def getBinaryFrame(hsv, lower_black, upper_black):
    ### Isolate our range of black pixels ###
    mask_for_black = cv2.inRange(hsv, lower_black, upper_black)
    black_pixels = cv2.findNonZero(mask_for_black)
    frame_binary = cv2.bitwise_not(mask_for_black) # invert
    return frame_binary, black_pixels

def drawCandidatePoints(display_img, candidates):
    for candidate in candidates:
        cv2.circle(display_img, (candidate[0], candidate[1]), 10, (0,0,255), -1)

def atImageBoundrary(coords, w, h):
    x, y = coords
    if x <= 0 or x>= w-1 or y <= 0 or y >= h-1:
        return True
    return False

def calcAngleWithHorizontal(origin_pt, final_pt):
    old_x = origin_pt[0]
    old_y = origin_pt[1]
    curr_x = final_pt[0] - old_x
    curr_y = -final_pt[1] + old_y
    angle = math.degrees(math.atan2(curr_y, curr_x))
    if final_pt[1] > origin_pt[1]:
        angle += 360

    return angle

def calcAvg(arr):
    if len(arr) == 0:
        return 0
    
    sum = 0
    for item in arr:
        sum += item
    return sum / len(arr)

def calcSlope(x1, y1, x2, y2):
    x_change = x2 - x1
    y_change = y2 - y1
    
    if x_change == 0:
        return 100 # vertical line
    else:
        return y_change / x_change

def createOneIndexedBorder(w, h):
    image_border = []

    # add top row from left to right
    for i in range(0, w):
        image_border.append((i, 0))
    # add right col from top to bottom
    for i in range(1, h):
        image_border.append((w-1, i))
    # add bottom row from left to right
    for i in range(w-2, -1, -1):
        image_border.append((i, h-1))
    # add left col from bottom to top
    for i in range(h-2, 0, -1):
        image_border.append((0, i))
    return image_border

def drawOnRobotMap(frame, robot_pos, destination_pxl, old_pos):
    cv2.circle(frame, old_pos, 20, (255,0,0), -1) # draw old pos point
    cv2.line(frame, old_pos, robot_pos, (255,0,0), 10) # draw orientation line
    cv2.circle(frame, robot_pos, 18, (0,255,0), -1) # Draw robot
    cv2.line(frame, robot_pos, destination_pxl, (0,0,255), 10) # draw line from line center to destination point
    cv2.circle(frame, destination_pxl, 18, (255,102,255), -1) # Draw destination

def getCandidates(intervals):
    candidates = []
    for interval in intervals:
        candidates.append((interval.midpoint_x, interval.midpoint_y))
    return candidates
    
def renderRobotMap(robotMap, window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, 0, 100)
    cv2.imshow(window_name, robotMap) # Original frame but with calculations
    cv2.waitKey(1)
