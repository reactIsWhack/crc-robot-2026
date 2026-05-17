import numpy as np
import cv2
from collections import deque
import math
from tools.utilities import atImageBoundrary, checkInRange, calcAngleWithHorizontal, calcEuclidianDist, calcAvg, calcSlope

colors = [(255,0,0), (0,75,150), (0,165,255),(0,0,0)]
distance = 5
black_threshold = 5 # number of times we see have to see black before changing direction
max_dist_traveled = 280

def computeCentroids(mask):
    # find the seperate blobs of white pixels on the green square mask. labels = blobs
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    '''
    stats.shape = (num_labels, 5)
    stats = [
        bg -> [x (top left), y (top left), blob width, blob height, blob area]
        label 1 -> [x (top left), y (top left), blob width, blob height, blob area]
        label 2 -> [x (top left), y (top left), blob width, blob height, blob area]
        ...
    ]
    centroids = [
        bg --> [x,y]
        label 1 --> [x,y]
        label 2 --> [x,y]
        ...
    ]
    total pixels = width * height
    area = width * height = total pixels
    '''
    green_sq_centroids = []
    for i in range(1, num_labels):
        total_pixels = stats[i][4] 
        cx, cy = centroids[i]

        if total_pixels > 10000:
            green_sq_centroids.append((cx, cy))
    return green_sq_centroids

def findGreenSquareLines(frame, edges):
    '''
    find the endpoints of the lines that surround the green squares using edge detection and houghlines
    '''
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=40, minLineLength=30, maxLineGap=40)
    if lines is None:
        return []
    
    green_square_lines = []
    for line in lines:
        # line = [[x1, y1, x2, y2]]
        x1, y1, x2, y2 = line[0]
        green_line_data = (x1, -y1, x2, -y2)
        green_square_lines.append(green_line_data)

    # print("green square lines before")
    # for line in green_square_lines:
    #     x1, y1, x2, y2 = line
    #     slope_a = calcSlope(x1, y1, x2, y2)
    #     y_intercept_a = -slope_a*x1 + y1
    #     print(f"slope={slope_a}, y-intercept={y_intercept_a}")
        
    # remove lines that are overlapping 
    # indexes_to_skip = set()
    # new_green_square_lines = []

    # for i in range(len(green_square_lines)):
    #     if i in indexes_to_skip:
    #         continue

    #     x1, y1, x2, y2 = green_square_lines[i]
    #     midpoint_a = ((x1+x2)/2, (y1+y2)/2)
    #     slope_a = calcSlope(x1, y1, x2, y2)
    #     y_intercept_a = -slope_a*x1 + y1

    #     for j in range(i + 1, len(green_square_lines)):
    #         if j in indexes_to_skip:
    #             continue

    #         x1b, y1b, x2b, y2b = green_square_lines[j]
    #         midpoint_b = ((x1b+x2b)/2, (y1b+y2b)/2)
    #         slope_b = calcSlope(x1b, y1b, x2b, y2b)
    #         y_intercept_b = -slope_b*x1b + y1b

    #         error_slope = 1.1
    #         error_intercept = 100
    #         dist_err = 100

    #         if (
    #             calcEuclidianDist(midpoint_a, midpoint_b) < dist_err
    #             and checkInRange(slope_a-error_slope, slope_a+error_slope, slope_b)
    #             and checkInRange(y_intercept_a-error_intercept, y_intercept_a+error_intercept, y_intercept_b)
    #         ):
    #             indexes_to_skip.add(j)

    #     new_green_square_lines.append(green_square_lines[i])
    
    # print("green square lines after")
    # for line in new_green_square_lines:
    #     x1, y1, x2, y2 = line
    #     slope_a = calcSlope(x1, y1, x2, y2)
    #     y_intercept_a = -slope_a*x1 + y1
    #     cv2.line(frame, (x1, -y1), (x2, -y2), (0,75,150),10)
        # print(f"slope={slope_a}, y-intercept={y_intercept_a}")
    # return a list of the endpoints of each line that borders a green square
    return green_square_lines

def solveFwdCandidates(candidate_angles):
    candidate_angles.sort()
    angle_change_threshold = 30

    for i in range(1, len(candidate_angles)):
        curr_angle = candidate_angles[i]
        prev_angle = candidate_angles[i - 1]
        if abs(curr_angle - prev_angle) > angle_change_threshold:
            first_half_len = i # 0 --> i - 1
            second_half_len = len(candidate_angles) - i # i --> len(candidate_angles)-1 
            candidate_angles = candidate_angles[0:i] if first_half_len > second_half_len else candidate_angles[i:] 
            break
    return calcAvg(candidate_angles)

def findFwdAngle(green_square_lines, h, w, x_old):
    line_data = []
    candidate_angles = []
    
    for line in green_square_lines:
        x1, y1, x2, y2 = line
        x_change = x2 - x1
        y_change = y2 - y1
        
        if x_change==0:
            candidate_angles.append(90)
            continue
        else:
            slope = y_change / x_change
            y_val = -(h - 1) # bottom row
            x_bottom = -1 if slope == 0 else int((y_val - y1 + slope * x1)/slope)
            # print(f"slope={slope}, x_bottom={x_bottom}")
                        
        if x_bottom < 0 or x_bottom >= w:
            # print("Out of bounds")
            continue

        y1 = -y1
        y2=-y2
        origin_pt = (x1, y1)
        final_pt = (x2, y2)
        if y2 > y1:
            temp = final_pt
            final_pt = origin_pt
            origin_pt = temp
        angle = calcAngleWithHorizontal(origin_pt, final_pt)
        # print(f"angle={angle}")
        # print()
        candidate_angles.append(angle)

    return solveFwdCandidates(candidate_angles)

def moveFwd(initial_coords, angle, fwdDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0]+distance_x), int(initial_coords[1]-distance_y))
    if atImageBoundrary(final_coords, w, h):
        fwdDone = True
    else:
        cv2.circle(frame, final_coords, 10, (0,0,255), -1)
        pass
    
    return (final_coords[0], final_coords[1], fwdDone)

def moveBwd(initial_coords, angle, bwdDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0] - distance_x), int(initial_coords[1] + distance_y))
    if atImageBoundrary(final_coords, w, h):
        bwdDone = True
    else:
        cv2.circle(frame, final_coords, 10, (255,0,255), -1)
    return (final_coords[0], final_coords[1], bwdDone)

def moveRight(initial_coords, angle, rightDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0] + distance_x), int(initial_coords[1] + distance_y))
    if atImageBoundrary(final_coords, w, h):
        rightDone = True
    else:
        cv2.circle(frame, final_coords, 10, (255,0,0), -1)
    return (final_coords[0], final_coords[1], rightDone)
    
def moveLeft(initial_coords, angle, leftDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0] - distance_x), int(initial_coords[1] - distance_y))
    if atImageBoundrary(final_coords, w, h):
        leftDone = True
    else:
        cv2.circle(frame, final_coords, 10, (255,255,255), -1)
    return (final_coords[0], final_coords[1], leftDone)

def identifyGreenSquarePosition(centroid, fwd_angle, binary_frame, w, h, frame, green_mask):
    leftDone = rightDone = fwdDone = bwdDone = False
    lpos_x = rpos_x = fpos_x = bpos_x = centroid[0]
    lpos_y = rpos_y = fpos_y = bpos_y = centroid[1]
    bwd = fwd = left = right = False
    left_cnt = right_cnt = fwd_cnt = bwd_cnt = 0
    total_dist_traveled = 0
    while total_dist_traveled < max_dist_traveled:
        fpos_x, fpos_y, fwdDone = moveFwd((fpos_x, fpos_y), math.radians(fwd_angle),fwdDone, w, h, frame)
        bpos_x, bpos_y, bwdDone = moveBwd((bpos_x, bpos_y), math.radians(fwd_angle),bwdDone, w, h, frame)
        lpos_x, lpos_y, leftDone = moveLeft((lpos_x, lpos_y), math.radians(90-fwd_angle),leftDone, w, h, frame)
        rpos_x, rpos_y, rightDone = moveRight((rpos_x, rpos_y), math.radians(90-fwd_angle),rightDone, w, h, frame)
        if not fwdDone and binary_frame[fpos_y][fpos_x] == 0 and green_mask[fpos_y][fpos_x] == 0:
            fwd_cnt += 1
        if not bwdDone and binary_frame[bpos_y][bpos_x] == 0 and green_mask[bpos_y][bpos_x] == 0:
            bwd_cnt += 1
        if not leftDone and binary_frame[lpos_y][lpos_x] == 0 and green_mask[lpos_y][lpos_x] == 0:
            left_cnt += 1
        if not rightDone and binary_frame[rpos_y][rpos_x] == 0 and green_mask[rpos_y][rpos_x] == 0:
            right_cnt += 1
        total_dist_traveled += distance
    position = None
    print(f"left={left_cnt}, right={right_cnt}, fwd={fwd_cnt}, bwd={bwd_cnt}")
    if left_cnt > right_cnt and (fwd_cnt > bwd_cnt or bwd_cnt == 0):
        position = "BR"
    elif right_cnt > left_cnt or (fwd_cnt > bwd_cnt or bwd_cnt == 0):
        position = "BL"
    elif right_cnt > left_cnt or (bwd_cnt > fwd_cnt or fwd_cnt == 0):
        position = "TL"
    elif left_cnt > right_cnt or (bwd_cnt > fwd_cnt or fwd_cnt == 0):
        position = "TR"
    return position

def updateStateOnGreenSquares(centroids, fwd_angle, binary_frame, w, h, frame, lineFollowState, green_mask):
    greenSquareStates = {
        "BR": False,
        "BL": False,
        "TR": False,
        "TL": False
    }
    for centroid in centroids:
        centroid_type = identifyGreenSquarePosition(centroid, fwd_angle, binary_frame, w, h, frame, green_mask)
        # print(f"centroid type = {centroid_type}")
        if centroid_type is not None:
            greenSquareStates[centroid_type] = centroid
    # print(f"green square states={greenSquareStates}")
    if greenSquareStates["BL"] and greenSquareStates["BR"]:
        lineFollowState = "U-turn"
    elif (greenSquareStates["BL"] or (lineFollowState == "green-square-turnleft" and greenSquareStates["TL"])):
        lineFollowState = "green-square-turnleft"
    elif (greenSquareStates["BR"] or (lineFollowState == "green-square-turnright" and greenSquareStates["TR"])):
        lineFollowState = "green-square-turnright"
    else:
        if lineFollowState == "green-square-turnleft"  or lineFollowState == "green-square-turnright" or lineFollowState == "regular-turn":
            lineFollowState = "regular-turn"
        else:
            lineFollowState = "normal"
    return greenSquareStates, lineFollowState

def exploreImageBorderClockwise(old_pos_idx, candidates, image_border):
    # search from old_pos to the end
    destination_pxl = None
    for i in range(old_pos_idx, len(image_border)):
        pxl = image_border[i]
        if pxl in candidates:
            destination_pxl = pxl
            break
    if destination_pxl is None:
        # search from 0 to the old pos
        for i in range(0, old_pos_idx):
            pxl = image_border[i]
            if pxl in candidates:
                destination_pxl = pxl
                break
    return destination_pxl

def exploreImageBorderCounterClockwise(old_pos_idx, candidates, image_border):
    # search from old_pos to 0 
    destination_pxl = None
    for i in range(old_pos_idx, -1, -1):
        pxl = image_border[i]
        if pxl in candidates:
            destination_pxl = pxl
            break
    # search from the end to the old pos
    if destination_pxl is None:
        # search from 0 to the old pos
        for i in range(len(image_border)-1, old_pos_idx, -1):
            pxl = image_border[i]
            if pxl in candidates:
                destination_pxl = pxl
                break
    return destination_pxl