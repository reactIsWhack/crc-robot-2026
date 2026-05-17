import cv2
import numpy as np

lower_black_center = (0, 0, 0)
# rgb_upper_black = np.uint8([[[224, 224, 211]]])
# hsv_upper_black = cv2.cvtColor(rgb_upper_black, cv2.COLOR_RGB2HSV)
upper_black_center = (180, 225, 170)

lower_black_edges = (0,0,0)
upper_black_edges = (180,225,65)

def getStartAndEndPositions(width, height, frame):
    left_dist = 90
    right_dist = 120
    up_dist = 80
    down_dist = 160


    row_start = (height//2) - up_dist
    row_end = (height//2) + down_dist
    col_start = (width//2) - left_dist
    col_end = (width//2) + right_dist
    cv2.rectangle(frame, (col_start, row_start), (col_end, row_end), (0,255,0), 12)

    return row_start, row_end, col_start, col_end

def breakUpFrame(width, height, frame_hsv, rstart, rend, cstart, cend):
    # frame is in hsv
    center_piece = frame_hsv[rstart:rend+1, cstart:cend+1]
    # cv2.imshow("Center Peice", cv2.cvtColor(center_piece, cv2.COLOR_HSV2BGR))
    left = frame_hsv[0:height, 0:cstart]
    mid_top = frame_hsv[0:rstart, cstart:cend+1]
    mid_bottom = frame_hsv[rend+1:height, cstart:cend+1]
    right = frame_hsv[0:height, cend+1:width]

    return (left, right, mid_top, mid_bottom, center_piece)

def mergeRows(row_a, row_b, row_c, full_mask):
    full_row = np.concatenate((row_a, row_b, row_c))
    full_mask.append(full_row)
    return full_mask

def createMask(width, height, frame_hsv, frame):
    row_start, row_end, col_start, col_end = getStartAndEndPositions(width, height, frame)

    left, right, mid_top, mid_bottom, center_piece = breakUpFrame(width, height, frame_hsv, row_start, row_end, col_start, col_end)
    left_mask = cv2.inRange(left, lower_black_edges, upper_black_edges)
    right_mask = cv2.inRange(right, lower_black_edges, upper_black_edges)
    mid_top_mask = cv2.inRange(mid_top, lower_black_edges, upper_black_edges)
    mid_bottom_mask = cv2.inRange(mid_bottom, lower_black_edges, upper_black_edges)
    center_mask = cv2.inRange(center_piece, lower_black_center, upper_black_center)
    # center_mask = ~center_mask.astype(np.uint8)

    full_mask = np.zeros((height, width))
    # cv2.imshow("Center Mask", center_mask)

    for row in range(0, row_start):
        left_row, mt_row, right_row = left_mask[row], mid_top_mask[row], right_mask[row]
        full_row = np.concatenate((left_row, mt_row, right_row))
        full_mask[row] = full_row

    for row in range(row_start, row_end+1):
        left_row, center_row, right_row = left_mask[row], center_mask[row-row_start], right_mask[row]
        full_row = np.concatenate((left_row, center_row, right_row))
        full_mask[row] = full_row

    for row in range(row_end+1, height):
        left_row, mb_row, right_row = left_mask[row], mid_bottom_mask[row-(row_end+1)], right_mask[row]
        full_row = np.concatenate((left_row, mb_row, right_row))
        full_mask[row] = full_row

    black_pixels = cv2.findNonZero(full_mask)
    black_pixels = black_pixels if black_pixels is not None else []
    frame_binary = ~full_mask.astype(np.uint8)
    # cv2.imshow("full mask", frame_binary)
    cv2.waitKey(1)
    return frame_binary, black_pixels
