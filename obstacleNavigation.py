import vl53l5cx_ctypes 
import numpy as np
from tools.utilities import calcAvg

tof_front = vl53l5cx_ctypes.VL53L5CX() # default i2c address is 0x29

# sensor2 = vl53l5cx.vl53l5cx(i2c_address=0x2A) <--- for changing i2c address; each tof gets its own i2c address
grid_size = 8
tof_front.set_resolution(grid_size*grid_size)
tof_front.start_ranging()

while True:
    if tof_front.data_ready(): # check if the tof sensor has finished capturing a frame. If so, we want to read the distance measurements
        # measurement.distance_mm is a 1D, grid_size * grid_size length array of integers
        measurement = tof_front.get_ranging_data()
        # convert measurement into a 2D array, with rows = grid_size and cols = grid_size
        grid = np.array(measurement.distance_mm).reshape(grid_size, grid_size)
        # first col = 0, last col = 7, middle columns = 3, 4
        # first row = 0, last row = 7, middle rows = 3, 4
        middle_first = grid_size//2
        middle_second = grid_size//2 + 1
        distance = calcAvg(np.concatenate((grid[middle_first, middle_first:middle_second+1], grid[middle_second, middle_first:middle_second+1])))


