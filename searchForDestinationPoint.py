import cv2
import numpy as np
import math
from newMotors import moveRobotLeft, moveRobotRight, moveRobotFwdOrBwd
print("imported search for destination point")

def rfind(l,target):
    try:
        l = l[::-1]
        index_in_reversed = l.index(target)
        original_index = len(l) - index_in_reversed - 1
        return original_index
    except ValueError:
        return 0

def find(l,target):
    try:
        return l.index(target)
    except ValueError:
        return 0

def searchBlack(start,direction,row):
    row = row.tolist()
    if direction == "left":
        return (start + rfind(row[:start+1],255)) // 2
    elif direction == "right":
        return (start + start+find(row[start:],255)) // 2
    else:
        return (rfind(row[:start+1],255) + start+find(row[start:],255)) // 2

def searchBeen(bin_img, start_idx, row, width):    
    
    i = start_idx + 1

    if bin_img[row][start_idx] == 0:
        return searchBlack(start_idx,"",bin_img[row])

    while True:
        
        right_pxl = None
        prevr_pxl = None
        left_pxl = None
        prevl_pxl = None

        if start_idx+i < width:
            right_pxl = bin_img[row][start_idx+i]
            prevr_pxl = bin_img[row][start_idx+i-1]
        if start_idx-i >= 0:
            left_pxl = bin_img[row][start_idx-i]
            prevl_pxl = bin_img[row][start_idx-i+1]
        if right_pxl is None and left_pxl is None:
            return 0

        # change from white to black
        if prevr_pxl == 255 and right_pxl == 0:
            return searchBlack(start_idx+i, "right", bin_img[row])

        if prevl_pxl == 255 and left_pxl == 0:
            return searchBlack(start_idx-i, "left", bin_img[row])

        i += 1
        
    return "uh oh"

def findOldPos(prev_old_pos, avg_pxls_bottom, frame_copy):
    # prev_old_pos is the column value of the previous old pos
    min_dist = 2e9
    old_pos = None
    for pxl in avg_pxls_bottom:
        dist = abs(pxl[0] - prev_old_pos)
        if dist < min_dist:
            old_pos = pxl
    cv2.circle(frame_copy, old_pos, 25, (203,192,255), -1)
    return old_pos
            


def searchRows(bin_img, row, width, display_img):    
    avg_pxls = []

    start = 0 if bin_img[row][0] == 0 else None
    
    for i in range(1, width):
        curr_pxl = bin_img[row][i]
        prev_pxl = bin_img[row][i - 1]

        # change from white to black --> start
        if prev_pxl == 255 and curr_pxl == 0:
            start = i
        
        # change from black to white --> end
        if (i == width - 1 or (curr_pxl == 0 and bin_img[row][i+1] == 255)) and start is not None:
            avg_pxl = (int((start + i)/2), row)
            cv2.circle(display_img, avg_pxl, 18, (0,0,255),-1)
            avg_pxls.append(avg_pxl)
            start = None
    # coordinates are (col, row) format
    return avg_pxls
    
def searchCols(bin_img, col, height, display_img):
    avg_pxls = []

    start = 0 if bin_img[0][col] == 0 else None
    
    for i in range(1, height):
        curr_pxl = bin_img[i][col]
        prev_pxl = bin_img[i-1][col]

        # change from white to black --> start
        if prev_pxl == 255 and curr_pxl == 0:
            start = i
        
        # change from black to white --> end
        if (i == height - 1 or (curr_pxl == 0 and bin_img[i+1][col] == 255)) and start is not None:
            avg_pxl = (col, int((start+i)/2))
            cv2.circle(display_img, avg_pxl, 18, (0,0,255),-1)
            avg_pxls.append(avg_pxl)
            start = None
    return avg_pxls

def calcAngleWithHorizontal(origin_pt, final_pt, display_img):
    old_x = origin_pt[0]
    old_y = origin_pt[1]
    curr_x = final_pt[0] - old_x
    curr_y = -final_pt[1] + old_y
    angle = math.degrees(math.atan2(curr_y, curr_x))
    if final_pt[1] > origin_pt[1]:
        angle += 360

    return angle

def determineDestinationPoint(avg_pixels, robot_pos, robot_orientation, display_img, old_pos):
    min_diff = 2e9
    destination_pxl = None
    destination_angle = None
    for pixel in avg_pixels:
        if pixel == None or pixel == old_pos:
            continue

        angle = calcAngleWithHorizontal(robot_pos, pixel, display_img)
        diff = abs(angle - robot_orientation)
        # print(pixel, angle, diff)
        if diff < min_diff:
            destination_pxl = pixel
            min_diff = diff
            destination_angle = angle
    
    cv2.line(display_img, robot_pos, destination_pxl, (0,0,255), 10)
    cv2.putText(display_img, str(destination_angle)[0:6]+" deg", (robot_pos[0]+45, robot_pos[1]-70), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (128,0,128), 5, cv2.LINE_AA)
    return (destination_pxl, destination_angle)

def moveToDestinationPoint(rotation_angle):
    direction = 'right' if rotation_angle < 90 or rotation_angle > 270 else 'left'

    error = 25
    if rotation_angle < 90 - error or rotation_angle > 90 + error:
        # keep rotating the robot
        if direction == 'right':
            moveRobotRight()
        else:
            moveRobotLeft()
    else:
        moveRobotFwdOrBwd("fwd")
    
        
     
    