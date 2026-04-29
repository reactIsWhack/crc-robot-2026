import numpy as np
import cv2
from collections import deque
import math
import time
from utilities import atImageBoundrary, checkInRange, calcAngleWithHorizontal, calcEuclidianDist, calcAvg

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

def findLineSlopes(frame, edges):
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
    avg_slope_a = calcAvg(slope_a)
    avg_slope_b = calcAvg(slope_b)
    return (avg_slope_a, avg_slope_b)

def exploreLineToRight(slope, centroid, frame_binary, w, h):
    cx, cy = centroid
    cy = cy * -1
    for x in range(cx, w, 3):
        y = abs(slope * (x - cx) + cy)
        if not checkInRange(0, h-1, y):
            return None
        
        pixel = frame_binary[y][x]
        if pixel == 0:
            return (x,y) # return coordinates of where black was found
    return None

def exploreLineToLeft(slope, centroid, frame_binary, h):
    cx, cy = centroid
    centroid *= -1
    for x in range(cx, 0, -3):
        y = abs(slope * (x - cx) + cy)
        if not checkInRange(0, h-1, y):
            return None
        
        if frame_binary[y][x] == 0:
            return (x, y) # return coordinates of where black was found
    return None

def identifyGreenSquarePos(point, centroid):
    x, y = point
    cx, cy = centroid
    '''
    If black spotted above centroid (smaller y) and tiny change in x = bottom green square. 
    If black spotted below centroid (greater y) and tiny change in x = top green square. 
    If black spotted right of centroid (greater x) and tiny change in y = left green square. 
    If black to left of centroid (smaller x) and tiny change in y = right green square
    
    '''
    change_threshold = 35
    x_change = abs(x - cx)
    y_change = abs(y - cy)
    if y < cy and x_change < change_threshold:
        return "bottom"
    elif y > cy and x_change < change_threshold:
        return "top"
    elif x > cx and y_change < change_threshold:
        return "left"
    elif x < cx and y_change < change_threshold:
        return "right"

def exploreGreenSquare(centroid, slope_a, slope_b, frame_binary, width, height):
    pt_1 = exploreLineToRight(slope_a, centroid, frame_binary, width, height)
    pt_2 = exploreLineToLeft(slope_a, centroid, frame_binary, height)
    pt_3 = exploreLineToRight(slope_b, centroid, frame_binary, width, height)
    pt_4 = exploreLineToLeft(slope_b, centroid, frame_binary, height)
    points = [pt_1, pt_2, pt_3, pt_4]
    # top, bottom, left, right
    positions = []
    position_dict = {["top","left"]: "TL", ["top","right"]: "TR", ["bottom", "right"]: "BR", ["bottom", "left"]: "BL"}
    horizontal_axis_angles = []
    vertical_axis_angles = []

    # check each point
    for pt in points:
        if pt is None:
            continue
        greenSquarePos = identifyGreenSquarePos(pt, centroid)
        positions.append(greenSquarePos)
        if greenSquarePos == "top" or greenSquarePos == "bottom":
            # fwd/bwd axis
            final_pt = (centroid[0] + 1, abs(-centroid[1])+slope_a)
            angle = calcAngleWithHorizontal(centroid, final_pt)
            vertical_axis_angles.append(angle)
        if greenSquarePos == "left" or greenSquarePos == "right":
            # left/right axis
            final_pt = (centroid[0] + 1, abs(-centroid[1])+slope_b)
            angle = calcAngleWithHorizontal(centroid, final_pt)
            horizontal_axis_angles.append(angle)
            
    avg_horizontal_angle = calcAvg(horizontal_axis_angles)
    avg_vertical_angle = calcAvg(vertical_axis_angles)
    position = position_dict[positions]
    return (position, avg_horizontal_angle, avg_vertical_angle)
            

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

def processGreenSquares(centroids, slope_a, slope_b, frame_binary, w, h):
    green_squares_present = {"TL": False, "TR": False, "BR": False, "BL": False}
    horizontal_angles = []
    vertical_angles = []
    for centroid in centroids:
        position, horizontal_angle, vertical_angle = exploreGreenSquare(centroid, slope_a, slope_b, frame_binary, w, h)
        green_squares_present[position] = True
        if horizontal_angle != 0:
            horizontal_angles.append(horizontal_angle)
        if vertical_angle != 0:
            vertical_angles.append(vertical_angle)
    horizontal_angle = calcAvg(horizontal_angles)
    vertical_angle = calcAvg(vertical_angles)
    
    if green_squares_present["BL"] and green_squares_present["BR"]:
        # U-Turn
        return "U-turn"
    elif green_squares_present["BL"] and not green_squares_present["BR"]:
        # go to green
        return "BL-square"
    elif not green_squares_present["BL"] and green_squares_present["BR"]:
        return "BR-square"
    else:
        return "normal"