import numpy as np
import cv2
from collections import deque
import math
import time
from utilities import atImageBoundrary, checkInRange, calcAngleWithHorizontal, calcEuclidianDist

colors = [(255,0,0), (0,75,150), (0,165,255),(0,0,0)]
distance = 5

def organizeGreenSquarePoints(mask, green_pixels, frame, h ,w):

    '''
    run a BFS algorithm to find all pixels that belong
    to a green square, and returns a 2D list containing
    all pairs of points [x,y] that belong to the ith square
    '''

    visited = np.full((h, w), False, dtype=bool)
    square_groups = []
    cv2.imshow("mask", mask)

    for pxl in green_pixels:
        # first element is col, second element is row
        row = pxl[0][1]
        col = pxl[0][0]

        # make pxl the start pxl, if not already visited
        if not visited[row][col]:
            group = [(row, col)]
            visited[row][col] = True
            q = deque()
            q.append((row, col))

            while len(q) > 0:
                row, col = q[0]
                neighbors = [(row,col-1), (row,col+1), (row+1,col),(row-1,col)]
                for neighbor in neighbors:
                    r, c = neighbor
                    if r >= h or r < 0 or c >= w or c < 0:
                        continue
                    if not visited[r][c] and mask[r][c] == 255:
                        visited[r][c] = True
                        group.append((r, c))
                        q.append((r, c))
                q.popleft()
            if len(group) > 2500:
                square_groups.append(group)
            # print(f"Num pixels in group: {len(group)}")

    # print(f"Total # groups: {len(square_groups)}")
    # for i, square_group in enumerate(square_groups):
    #     for pxl in square_group:
    #         cv2.circle(frame, (pxl[1], pxl[0]), 2, colors[i%4], -1)
    return square_groups

def determineFwdAngle(square_group, frame, edges):
    '''
    1. for each green square, find the slope of the two black lines surrounding it (edge detection on mask to identify boundraries where mask changes b/w white and then HoughLines to get the line segments)
    Sort the slopes of the line segments and split the list when there is a large change. then, get the averages of each of the two lists, giving us two slopes for the two lines. 
    2. Develop an equation for each of the two lines with point slope form, where the point is the centroid
    3. Explore along each line, starting at the centroid by increasing and decreasing x
    4. If black spotted above centroid (smaller y) and tiny change in x = bottom green square. 
        If black spotted below centroid (greater y) and tiny change in x = top green square. 
        If black spotted right of centroid (greater x) and tiny change in y = left green square. 
        If black to left of centroid (smaller x) and tiny change in y = right green square
    5. IF we found a top or bottom while traveling along the line, the line must be the fwd/bwd axis. If we found left or right while traveling along the line, the line must be the left/right axis.
    Get the angle of each of these axes.
    '''
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
    slopes = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        y1 = -y1
        y2=-y2
        slope = (y2 - y1) / (x2 - x1)
        slopes.append(slope)
        cv2.line(frame, (x1, y1), (x2, y2), (0,75,150),10)
    slopes.sort()

    slope_change_threshold = 3
    slope_a = []
    slope_b = []
    for i in range(1, len(slopes)):
        curr_slope = abs(slopes[i]) 
        prev_slope = abs(slopes[i - 1])
        if abs(curr_slope - prev_slope) >= slope_change_threshold:
            slope_a = slopes[0:i]
            slope_b = slopes[i+1:]
            break
    print(slope_a, slope_b)
        

def findLineDirection(square_groups, frame, edges):
   

def computeCentroids(square_groups, frame):
    centroids = []
    for i, square_group in enumerate(square_groups):
        r_sum = c_sum = 0
        for pixel in square_group:
            r_sum += pixel[0]
            c_sum += pixel[1]
            
        centroid_row = int(r_sum / len(square_group))
        centroid_col = int(c_sum / len(square_group))
        cv2.circle(frame, (centroid_col, centroid_row), 18, colors[i], -1)
        centroids.append((centroid_col, centroid_row))
    return centroids

def moveFwd(initial_coords, angle, fwdDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0]+distance_x), int(initial_coords[1]-distance_y))
    if atImageBoundrary(final_coords, w, h):
        fwdDone = True
    else:
        pass
        # cv2.circle(frame, final_coords, 10, (0,0,255), -1)
    
    return (final_coords[0], final_coords[1], fwdDone)

def moveBwd(initial_coords, angle, bwdDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0] - distance_x), int(initial_coords[1] + distance_y))
    if atImageBoundrary(final_coords, w, h):
        bwdDone = True
    else:
        pass
        # cv2.circle(frame, final_coords, 10, (255,0,255), -1)
    return (final_coords[0], final_coords[1], bwdDone)

def moveRight(initial_coords, angle, rightDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0] + distance_x), int(initial_coords[1] + distance_y))
    if atImageBoundrary(final_coords, w, h):
        rightDone = True
    else:
        pass
        # cv2.circle(frame, final_coords, 10, (255,0,0), -1)
    return (final_coords[0], final_coords[1], rightDone)
    
def moveLeft(initial_coords, angle, leftDone, w, h, frame):
    distance_x = distance*math.cos(angle)
    distance_y = distance*math.sin(angle)
    final_coords = (int(initial_coords[0] - distance_x), int(initial_coords[1] - distance_y))
    if atImageBoundrary(final_coords, w, h):
        leftDone = True
    else:
        pass
        # cv2.circle(frame, final_coords, 10, (255,255,255), -1)
    return (final_coords[0], final_coords[1], leftDone)

def identifyGreenSquarePosition(centroid, lineDirection, binary_frame, w, h, frame):
    leftDone = rightDone = fwdDone = bwdDone = False
    lpos_x = rpos_x = fpos_x = bpos_x = centroid[0]
    lpos_y = rpos_y = fpos_y = bpos_y = centroid[1]
    bwd = fwd = left = right = False
    while not leftDone or not rightDone or not fwdDone or not bwdDone:
        fpos_x, fpos_y, fwdDone = moveFwd((fpos_x, fpos_y), math.radians(lineDirection),fwdDone, w, h, frame)
        bpos_x, bpos_y, bwdDone = moveBwd((bpos_x, bpos_y), math.radians(lineDirection),bwdDone, w, h, frame)
        lpos_x, lpos_y, leftDone = moveLeft((lpos_x, lpos_y), math.radians(90-lineDirection),leftDone, w, h, frame)
        rpos_x, rpos_y, rightDone = moveRight((rpos_x, rpos_y), math.radians(90-lineDirection),rightDone, w, h, frame)
        if not fwdDone and binary_frame[fpos_y][fpos_x] == 0:
            fwd = True
            fwdDone = True
        if not bwdDone and binary_frame[bpos_y][bpos_x] == 0:
            bwd = True
            bwdDone = True
        if not leftDone and binary_frame[lpos_y][lpos_x] == 0:
            left = leftDone = True
        if not rightDone and binary_frame[rpos_y][rpos_x] == 0:
            right = rightDone = True
    # left, right, fwd, bwd
    boolean = (left, right, fwd, bwd)
    boolean_to_pos = {(True, False, True, False):"BR",
                     (True, False, False, True):"TR",
                     (False, True, True, False):"BL",
                     (False, True, False, True):"TL"
                     }
    if boolean in boolean_to_pos.keys():
        return boolean_to_pos[boolean]
    else:
        return None

def processGreenSquares(centroids, lineDirection, mask, w, h, frame):
    greenSquareStates = {
        "BR": None,
        "BL": None,
        "TR": None,
        "TL": None
    }
    for centroid in centroids:
        centroid_type = identifyGreenSquarePosition(centroid, lineDirection, mask, w, h, frame)
        if centroid_type is not None:
            greenSquareStates[centroid_type] = centroid
    print(greenSquareStates)