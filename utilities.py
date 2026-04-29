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