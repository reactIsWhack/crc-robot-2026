import numpy as np
import cv2
from collections import deque
import math
from utilities import atImageBoundrary, checkInRange, calcAngleWithHorizontal, calcEuclidianDist, calcAvg

colors = [(255,0,0), (0,75,150), (0,165,255),(0,0,0)]
distance = 5
black_threshold = 25 # number of times we see have to see black before changing direction

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

def findGreenSquareLines(frame, edges):
    '''
    find the endpoints of the lines that surround the green squares using edge detection and houghlines
    '''
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
    green_square_lines = []
    for line in lines:
        # line = [[x1, y1, x2, y2]]
        x1, y1, x2, y2 = line[0]
        green_line_data = (x1, -y1, x2, -y2)
        green_square_lines.append(green_line_data)
        cv2.line(frame, (x1, y1), (x2, y2), (0,75,150),10)
    return green_square_lines

def findFwdAngle(green_square_lines, h, w, x_old):
    line_data = []
    for line in green_square_lines:
        x1, y1, x2, y2 = line
        slope = (y2 - y1) / (x2 - x1)
        y_val = -(h - 1) # bottom row
        x_bottom = int(abs((y_val - y1 + slope * x1)/slope))
        if x_bottom < 0 or x_bottom >= w:
            continue
        dist_to_oldpos = abs(x_old - x_bottom)
        line_data.append((dist_to_oldpos, x1, y1, x2, y2))
    line_data = sorted(line_data)
    x1 = line_data[0][1]
    x2 = line_data[0][3]
    y1 = -line_data[0][2] # change negative back to positive
    y2 = -line_data[0][4]

    origin_pt = (x1, y1)
    final_pt = (x2, y2)
    if y2 < y1:
        temp = final_pt
        final_pt = origin_pt
        origin_pt = temp
    return calcAngleWithHorizontal(origin_pt, final_pt)

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
        cv2.circle(frame, final_coords, 10, (0,0,255), -1)
    
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

def identifyGreenSquarePosition(centroid, fwd_angle, binary_frame, w, h, frame):
    leftDone = rightDone = fwdDone = bwdDone = False
    lpos_x = rpos_x = fpos_x = bpos_x = centroid[0]
    lpos_y = rpos_y = fpos_y = bpos_y = centroid[1]
    bwd = fwd = left = right = False
    while not leftDone or not rightDone or not fwdDone or not bwdDone:
        fpos_x, fpos_y, fwdDone = moveFwd((fpos_x, fpos_y), math.radians(fwd_angle),fwdDone, w, h, frame)
        bpos_x, bpos_y, bwdDone = moveBwd((bpos_x, bpos_y), math.radians(fwd_angle),bwdDone, w, h, frame)
        lpos_x, lpos_y, leftDone = moveLeft((lpos_x, lpos_y), math.radians(90-fwd_angle),leftDone, w, h, frame)
        rpos_x, rpos_y, rightDone = moveRight((rpos_x, rpos_y), math.radians(90-fwd_angle),rightDone, w, h, frame)
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

def updateStateOnGreenSquares(centroids, fwd_angle, mask, w, h, frame, lineFollowState):
    greenSquareStates = {
        "BR": False,
        "BL": False,
        "TR": False,
        "TL": False
    }
    for centroid in centroids:
        centroid_type = identifyGreenSquarePosition(centroid, fwd_angle, mask, w, h, frame)
        if centroid_type is not None:
            greenSquareStates[centroid_type] = centroid
    print(greenSquareStates)
    if greenSquareStates["BL"] and greenSquareStates["BR"] and lineFollowState == "normal":
        lineFollowState = "U-turn"
    elif greenSquareStates["BL"] and not greenSquareStates["BR"] and lineFollowState == "normal":
        lineFollowState = "green-square-turnleft"
    elif not greenSquareStates["BL"] and greenSquareStates["BR"] and lineFollowState == "normal":
        lineFollowState = "green-square-turnright"
    return greenSquareStates


def moveIntoBlackRegion(dir, binary_frame, pos, fwd_angle, w, h, frame):
    black_count = 0
    while black_count < black_threshold:
        x = y = done = 0
        if dir == "fwd":
            x, y, done = moveFwd(pos, fwd_angle, False, w, h, frame)
        elif dir == "left":
            x, y, done = moveLeft(pos, 90-fwd_angle, False, w, h, frame)
        elif dir == "right":
            x, y, done = moveRight(pos, 90-fwd_angle, False, w, h, frame)

        if binary_frame[y][x] == 0:
            black_count += 1
        pos = (x,y)
    return pos

def moveUntilEdge(dir, pos, fwd_angle, w, h, frame):
    done = False
    while not done:
        x = y = 0
        if dir == "fwd":
            x, y, done = moveFwd(pos, fwd_angle, False, w, h, frame)
        elif dir == "left":
            x, y, done = moveLeft(pos, 90-fwd_angle, False, w, h, frame)
        elif dir == "right":
            x, y, done = moveRight(pos, 90-fwd_angle, False, w, h, frame)
        pos = (x, y)
    return pos

def handleLeftTurn(greenSquareStates, fwd_angle, w, h, frame, binary_frame):
    destination = None
    
    if greenSquareStates["BL"]:
        # first move forward
        pos = moveIntoBlackRegion("fwd", binary_frame, greenSquareStates["BL"], fwd_angle, w, h, frame)
        # move left until at edge of image
        destination = moveUntilEdge("left", pos, fwd_angle, w, h, frame)
    elif greenSquareStates["TL"]:
        # first move right
        pos = moveIntoBlackRegion("right", binary_frame, greenSquareStates["TL"], fwd_angle, w, h, frame)
        # move fwd until at edge of image
        destination = moveUntilEdge("fwd", pos, fwd_angle, w, h, frame)
    return destination

def handleRightTurn(greenSquareStates, fwd_angle, w, h, frame, binary_frame):
    destination = None
    
    if greenSquareStates["BR"]:
        # first move forward
        pos = moveIntoBlackRegion("fwd", binary_frame, greenSquareStates["BR"], fwd_angle, w, h, frame)
        # move right until at edge of image
        destination = moveUntilEdge("right", pos, fwd_angle, w, h, frame)
    elif greenSquareStates["TL"]:
        # first move left
        pos = moveIntoBlackRegion("left", binary_frame, greenSquareStates["TL"], fwd_angle, w, h, frame)
        # move fwd until at edge of image
        destination = moveUntilEdge("fwd", pos, fwd_angle, w, h, frame, binary_frame)
    return destination