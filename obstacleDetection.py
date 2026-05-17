from vl53l5cx_ctypes import VL53L5CX
import board
import busio
from vl53l5cx_ctypes import VL53L5CX
from gpiozero import OutputDevice
import time
import numpy as np
from newMotors import move

i2c = busio.I2C(board.SCL, board.SDA)

def init_l5cx():
    xshut_l5cx  = OutputDevice(8)
    xshut_l0x_side = OutputDevice(11)
    xshut_l0x_top1 = OutputDevice(9)
    xshut_l0x_top2 = OutputDevice(10)

    # turn off all sensors immediately
    xshut_l5cx.off()
    xshut_l0x_side.off()
    xshut_l0x_top1.off()
    xshut_l0x_top2.off()
    time.sleep(1.0)
    
    print("uploading firmware matrix over I2C...")
    try:
        # Connects to default I2C Bus 1, Address 0x29
        sensor = VL53L5CX()
        
        # Configure matrix resolution: 64 standard zones (8x8 grid)
        sensor.set_resolution(8 * 8)
        
        # Configure update rate: 15Hz is max speed for 8x8 resolution
        sensor.set_ranging_frequency_hz(15)
        
        # Boot the physical VCSEL laser emitter array
        sensor.start_ranging()
        print("L5CX is online!")
        return sensor
        
    except RuntimeError as error:
        print(f"failed to start l5cx: {error}")
        return None

def getFrontDistance():
    frontSensor = init_l5cx()

    if frontSensor.data_ready():
        data = frontSensor.get_data()
        distance_grid = np.array(data.distance_mm).reshape(8,8)
        return distance_grid[3][3]
    return -1


def detectObstacle(line_follow_state):
    threshold = 40
    if getFrontDistance() <= threshold:
        line_follow_state = "obstacle"
    return line_follow_state

def navigateAroundObstacle():
    m
