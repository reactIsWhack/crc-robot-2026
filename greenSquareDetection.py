import numpy as np
import cv2
from collections import deque
import math

colors = [(255,0,0), (0,75,150), (0,165,255),(0,0,0)]

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
            #print(f"Num pixels in group: {len(group)}")

    #print(f"Total # groups: {len(square_groups)}")
    # for i, square_group in enumerate(square_groups):
    #     for pxl in square_group:
    #         cv2.circle(frame, (pxl[1], pxl[0]), 2, colors[i%4], -1)
    return square_groups

def computeCentroids(square_groups, frame):
    centroids = []
    for i, square_group in enumerate(square_groups):
        r_sum = c_sum = 0
        for pixel in square_group:
            r_sum += pixel[0]
            c_sum += pixel[1]
            
        centroid_row = int(r_sum / len(square_group))
        centroid_col = int(c_sum / len(square_group))
        # cv2.circle(frame, (centroid_col, centroid_row), 18, colors[i], -1)
        centroids.append((centroid_col, centroid_row))
    return centroids

def findLineDirection(old_pos, desired_pos, frame_copy, robot_pos):
    # shift the old pos to the origin --> subtract the old x position and add the old y position
    x = desired_pos[0] - old_pos[0] # desired x position - old x position
    y = desired_pos[1] + old_pos[1] # desired y position + old y position
    theta = math.degrees(math.atan2(y, x))

    cv2.putText(frame_copy, str(theta)[0:6]+" deg", (robot_pos[0]-300, robot_pos[1]), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (128,0,128), 5, cv2.LINE_AA)
    cv2.line(frame_copy, old_pos, desired_pos, (200,2000,200),10)
    return theta

def checkFwdForBlack(frame_copy, line_direction, bin_frame, height, width, centroids):
    # convert line direction to radians
    theta = math.radians(line_direction)
    top = []
    for centroid in centroids:
        centroid_x = centroid[0]
        centroid_y = centroid[1]
        d = 5
        while True:
            vertical_dist = d * math.sin(theta)
            horizontal_dist = d * math.cos(theta)
            new_x = int(centroid_x + horizontal_dist)
            new_y = int(centroid_y - vertical_dist)

            if new_x < 0 or new_x >= width or new_y < 0 or new_y >= height:
                break
            # print(new_x, new_y)
            pxl = bin_frame[new_y][new_x]
            # if black is found, then the current centroid belongs to a bottom green square
            if pxl == 0:
                top.append(centroid)
                cv2.circle(frame_copy, centroid, 18, (128,0,128), -1)
                break
            d+=5

def checkBwdForBlack(frame_copy, line_direction, bin_frame, height, width, centroids):
    # convert line direction to radians
    theta = math.radians(line_direction)
    bottom = []
    for centroid in centroids:
        centroid_x = centroid[0]
        centroid_y = centroid[1]
        d = 5
        while True:
            angle = math.pi - theta if theta > 180 else theta
            vertical_dist = d * math.sin(math.pi - theta)
            horizontal_dist = d * math.cos(math.pi - theta)
            if theta < 90:
                horizontal_dist *= -1
            
            new_x = int(centroid_x + horizontal_dist)
            new_y = int(centroid_y + vertical_dist)

            if new_x < 0 or new_x >= width or new_y < 0 or new_y >= height:
                break
            # print(new_x, new_y)
            pxl = bin_frame[new_y][new_x]
            # if black is found, then the current centroid belongs to a bottom green square
            if pxl == 0:
                bottom.append(centroid)
                cv2.circle(frame_copy, centroid, 18, (0,75,150), -1)
                break
            d+=5



