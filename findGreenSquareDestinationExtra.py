def moveIntoBlackRegion(direction, binary_frame, pos, fwd_angle, w, h, frame):
    black_count = 0
    while black_count < black_threshold:
        x = y = done = 0
        if direction == "fwd":
            x, y, done = moveFwd(pos, math.radians(fwd_angle), False, w, h, frame)
        elif direction == "left":
            x, y, done = moveLeft(pos, math.radians(90-fwd_angle), False, w, h, frame)
        elif direction == "right":
            x, y, done = moveRight(pos, math.radians(90-fwd_angle), False, w, h, frame)

        if binary_frame[y][x] == 0:
            black_count += 1
            cv2.circle(frame, (x, y), 15, (255,0,255), -1)
        pos = (x,y)
    return pos

def moveUntilEdge(direction, pos, fwd_angle, w, h, frame):
    done = False
    while not done:
        x = y = 0
        if direction == "fwd":
            x, y, done = moveFwd(pos, math.radians(fwd_angle), False, w, h, frame)
        elif direction == "left":
            x, y, done = moveLeft(pos, math.radians(90-fwd_angle), False, w, h, frame)
        elif direction == "right":
            x, y, done = moveRight(pos, math.radians(90-fwd_angle), False, w, h, frame)
        cv2.circle(frame, pos, 15, (255,0,255), -1)
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
    print(greenSquareStates)
    
    if greenSquareStates["BR"]:
        # first move forward
        pos = moveIntoBlackRegion("fwd", binary_frame, greenSquareStates["BR"], fwd_angle, w, h, frame)
        # move right until at edge of image
        destination = moveUntilEdge("right", pos, fwd_angle, w, h, frame)
    elif greenSquareStates["TR"]:
        # first move left
        pos = moveIntoBlackRegion("left", binary_frame, greenSquareStates["TR"], fwd_angle, w, h, frame)
        # move fwd until at edge of image
        destination = moveUntilEdge("fwd", pos, fwd_angle, w, h, frame)
    return destination

def organizeGreenSquarePoints(mask, green_pixels, frame, h ,w):

    '''
    run a BFS algorithm to find all pixels that belong
    to a green square, and returns a 2D list containing
    all pairs of points [x,y] that belong to the ith square
    '''

    visited = np.full((h, w), False, dtype=bool)
    square_groups = []

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