
### Imports ###

import cv2
import numpy as np
import math
from collections import namedtuple
from utilities import calcAngleWithHorizontal

### Initialization
Interval = namedtuple("Interval", ["start_x", "end_x", "start_y", "end_y", "midpoint_x", "midpoint_y", "length", "type"])

def printIntervals(intervals):
    print(f"Num intervals: {len(intervals)}")
    for interval in intervals:
        print(f"start: ({interval.start_x}, {interval.start_y}), end: ({interval.end_x}, {interval.end_y}), midpoint: ({interval.midpoint_x}, {interval.midpoint_y}) len: {interval.length}")
    print()

def collectOuterIntervals(bin_img, width, height, greenPresent):
    left_intervals = searchRows(bin_img, width, 0)  # Assuming we're looking at the top row
    right_intervals = searchRows(bin_img, width, height - 1)  # Assuming we're looking at the bottom row
    top_intervals = searchCols(bin_img, 0, height)  # Assuming we're looking at the left column
    bottom_intervals = searchCols(bin_img, width - 1, height)  # Assuming we're looking at the right column
    
    intervals = []
    intervals.extend(left_intervals)
    intervals.extend(right_intervals)
    intervals.extend(top_intervals)
    intervals.extend(bottom_intervals)
    threshold = 75
    # print("Initial Intervals")
    # printIntervals(intervals)
    new_intervals = []
    for interval in intervals:
        if interval.length > threshold:
            new_intervals.append(interval)

    # if greenPresent:
        # new_intervals = mergeCornerIntervals(new_intervals, width, height)

    # print("Final Intervals")
    # printIntervals(new_intervals)
    return new_intervals

# Finds intervals at a given row
def searchRows(bin_img, width, row):
    intervals = []

    start = 0 if bin_img[row][0] == 0 else None
    # store intervals to eliminate smaller ones
    
    for i in range(1, width):
        curr_pxl = bin_img[row][i]
        prev_pxl = bin_img[row][i - 1]

        # change from white to black --> start of interval
        if prev_pxl == 255 and curr_pxl == 0:
            start = i
        
        # change from black to white or reached the end of the row --> end of interval
        if (i == width - 1 or (curr_pxl == 0 and bin_img[row][i+1] == 255)) and start is not None:
            interval = Interval(start_x=start, end_x=i, start_y=row, end_y=row, midpoint_x=(start + i) // 2, midpoint_y=row, length=i-start+1,type="")
            intervals.append(interval)
            start = None
    # coordinates are (col, row) format
    return intervals


# Finds intervals at a given column
def searchCols(bin_img, col, height):
    intervals = []

    start = 0 if bin_img[0][col] == 0 else None
    
    for i in range(1, height):
        curr_pxl = bin_img[i][col]
        prev_pxl = bin_img[i-1][col]

        # change from white to black --> start
        if prev_pxl == 255 and curr_pxl == 0:
            start = i
        
        # change from black to white --> end
        if (i == height - 1 or (curr_pxl == 0 and bin_img[i+1][col] == 255)) and start is not None:
            interval = Interval(start_x=col, end_x=col, start_y=start, end_y=i, midpoint_x=col, midpoint_y=(start+i)//2, length=i-start+1,type="")
            intervals.append(interval)
            start = None
    return intervals

def mergeMergedIntervals(mergedIntervals, width, height):
    newMergedIntervals = []
    isMerged = {"TL":False, "TR":False, "BL":False, "BR":False} # track which merged intervals have been merged or not
    for i in range(len(mergedIntervals)):
        intervalA = mergedIntervals[i]
        for j in range(i + 1, len(mergedIntervals)):
            intervalB = mergedIntervals[j]
            newInterval = None
            if intervalA.type == "BL" and intervalB.type == "BR":
                newInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=width//2, midpoint_y=height-1, length=intervalA.length+intervalB.length,type="BL-BR")
                isMerged["BL"] = True
                isMerged["BR"] = True
            elif intervalA.type == "BL" and intervalB.type == "TL":
                newInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=0, midpoint_y=height//2, length=intervalA.length+intervalB.length,type="BL-TL")
                isMerged["BL"] = True
                isMerged["TL"] = True
            elif intervalA.type == "TR" and intervalB.type == "BR":
                newInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=width-1, midpoint_y=height//2, length=intervalA.length+intervalB.length,type="BR-TR")
                isMerged["TR"] = True
                isMerged["BR"] = True
            elif intervalA.type == "TR" and intervalB.type == "TL":
                newInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=width//2, midpoint_y=0, length=intervalA.length+intervalB.length,type="TR-TL")
                isMerged["TR"] = True
                isMerged["TL"] = True
            if newInterval is not None:
                newMergedIntervals.append(newInterval)
    for key in isMerged.keys():
        if isMerged[key]:
            continue
        # if the interval has not been merged, keep it the same
        for interval in mergedIntervals:
            if interval.type == key:
                newMergedIntervals.append(interval)
    return newMergedIntervals

# Gets rid of adjacent intervals at corners
def mergeCornerIntervals(intervals, width, height):
    horizontalCornerIntervals = []
    verticalCornerIntervals = []
    merged = {}

    for interval in intervals:
        # check for vertical corner interval
        if interval.end_x - interval.start_x == 0 and (interval.start_y == 0 or interval.end_y == height-1):
            verticalCornerIntervals.append(interval)
        # check for horizontal corner interval
        if interval.end_y - interval.start_y == 0 and (interval.start_x == 0 or interval.end_x == width-1):
            horizontalCornerIntervals.append(interval)

        merged[interval] = False
    
    mergedIntervals = []
    # for each horizontal corner interval, check all the vertical corner intervals to see if the two intersect
    for horizontalCornerInterval in horizontalCornerIntervals:
        for verticalCornerInterval in verticalCornerIntervals:
            mergedInterval = None

            if horizontalCornerInterval.start_x == 0 and horizontalCornerInterval.start_y == 0 and verticalCornerInterval.start_x == 0 and verticalCornerInterval.start_y == 0:
                # top left intersection
                mergedInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=0, midpoint_y=0, length=horizontalCornerInterval.length+verticalCornerInterval.length,type="TL")
            elif horizontalCornerInterval.start_x == 0 and horizontalCornerInterval.start_y == height-1 and verticalCornerInterval.end_x == 0 and verticalCornerInterval.end_y == height-1:  
                # bottom left intersection
                mergedInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=0, midpoint_y=height-1, length=horizontalCornerInterval.length+verticalCornerInterval.length,type="BL")
            elif horizontalCornerInterval.end_x == width-1 and horizontalCornerInterval.end_y == 0 and verticalCornerInterval.start_x == width-1 and verticalCornerInterval.start_y == 0:
                # top right intersection
                mergedInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=width-1, midpoint_y=0, length=horizontalCornerInterval.length+verticalCornerInterval.length,type="TR")
            elif horizontalCornerInterval.end_x == width-1 and horizontalCornerInterval.end_y == height - 1 and verticalCornerInterval.end_x == width-1 and verticalCornerInterval.end_y==height-1:
                # bottom right intersection
                mergedInterval = Interval(start_x=-1, end_x=-1, start_y=-1, end_y=-1, midpoint_x=width-1, midpoint_y=height-1, length=horizontalCornerInterval.length+verticalCornerInterval.length,type="BR")
            
            if mergedInterval is not None:
                mergedIntervals.append(mergedInterval)
                merged[horizontalCornerInterval] = True
                merged[verticalCornerInterval] = True
    new_intervals = []
    for interval in merged.keys():
        if not merged[interval]:
            new_intervals.append(interval)
    new_intervals.extend(mergedIntervals)
    return new_intervals


def findOldPos(intervals, prev_old_pos):
    p_old_x = prev_old_pos[0]
    p_old_y = prev_old_pos[1]
    min_dist = 2e9
    old_pos = None
    
    # find the midpoint closest to the previous old pos to be the new old pos
    for interval in intervals:
        mid_x = interval.midpoint_x
        mid_y = interval.midpoint_y
        dist = math.sqrt((mid_x-p_old_x)**2 + (mid_y-p_old_y)**2)
        
        if dist < min_dist:
            old_pos = (mid_x, mid_y)
            min_dist = dist
            
    for interval in intervals:
        if old_pos is not None and interval.midpoint_x == old_pos[0] and interval.midpoint_y == old_pos[1]:
            intervals.remove(interval)
            break
    return old_pos, intervals

def determineDestinationPoint(candidates, robot_pos, robot_orientation, display_img, old_pos):
    min_diff = 2e9
    destination_pxl = None
    destination_angle = None
    for pixel in candidates:
        angle = calcAngleWithHorizontal(robot_pos, pixel)
        diff = abs(angle - robot_orientation)
        # print(pixel, angle, diff)
        if diff < min_diff:
            destination_pxl = pixel
            min_diff = diff
            destination_angle = angle
    
    cv2.line(display_img, robot_pos, destination_pxl, (0,0,255), 10)
    cv2.putText(display_img, str(destination_angle)[0:6]+" deg", (robot_pos[0]+45, robot_pos[1]-70), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (128,0,128), 5, cv2.LINE_AA)
    return (destination_pxl, destination_angle)
     
'''

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

def mergeCornerIntervals(intervals, width, height):
    
    toCheck = []
    
    for interval in intervals:
        if (
            interval.start_x == 0 or
            interval.end_x == width-1 or
            interval.start_y == 0 or
            interval.end_y == height-1
        ):
            toCheck.append(interval)
            intervals.remove(interval)

    # start_x = leftmost, start_y = topmost, end_x=rightmost, end_y=lowest
    for i in range(len(toCheck)):
        for j in range(i+1,len(toCheck)):
            if toCheck[i].start_x == 0 and toCheck[j].start_y == 0:
                # top left
                intervals.append(Interval(
                    start_x=toCheck[i].start_x, end_x=toCheck[j].end_x,
                    start_y=toCheck[i].end_y, end_y=toCheck[j].end_y,
                    midpoint_x=0, midpoint_y=0
                ))
                
            elif toCheck[i].end_x == width-1 and toCheck[j].start_y == 0:
                # top right 
                intervals.append(Interval(
                    start_x=toCheck[i].start_x, end_x=toCheck[j].end_x,
                    start_y=toCheck[i].start_y, end_y=toCheck[j].end_y,
                    midpoint_x=width-1, midpoint_y=0
                ))
            elif toCheck[i].end_x == width-1 and toCheck[j].end_y == height-1:
                # bottom right
                intervals.append(Interval(
                    start_x=toCheck[i].start_x, end_x=toCheck[j].end_x,
                    start_y=toCheck[i].start_y, end_y=toCheck[j].end_y,
                    midpoint_x=width-1, midpoint_y=height-1
                ))
            elif toCheck[i].start_x == 0 and toCheck[j].start_y == height-1:
                # bottom left
                intervals.append(Interval(
                    start_x=toCheck[i].start_x, end_x=toCheck[j].end_x,
                    start_y=toCheck[i].start_y, end_y=toCheck[j].end_y,
                    midpoint_x=0, midpoint_y=height-1
                ))
    return 
'''
    