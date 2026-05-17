import time
import board
import busio
import numpy as np
from gpiozero import OutputDevice
import adafruit_vl53l0x
from vl53l5cx_ctypes import VL53L5CX

i2c = busio.I2C(board.SCL, board.SDA)


### masks ###

lower_green = np.array([35, 60, 60])
upper_green = np.array([85, 255, 255])

### ###


def init_l5cx():
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

# stores sensor objects
sensors = {}

# # VL53L5CX
# xshut_l5cx.on() # Drives pin HIGH
# time.sleep(1.0)
# sensors["l5cx"] = init_l5cx() 

# # VL53L0X #1
# xshut_l0x_side.on()
# time.sleep(0.2)
# sensors["l0x_1"] = adafruit_vl53l0x.VL53L0X(i2c)
# sensors["l0x_1"].set_address(0x29) # Changes default 0x29 to 0x30
# time.sleep(0.2)

# # VL53L0X #2
# xshut_l0x_top1.on()
# time.sleep(0.2)
# sensors["l0x_2"] = adafruit_vl53l0x.VL53L0X(i2c)
# sensors["l0x_2"].set_address(0x29) # Changes default 0x29 to 0x31
# time.sleep(0.2)

# # VL53L0X #3
# xshut_l0x_top2.on()
# time.sleep(0.2)
# sensors["l0x_3"] = adafruit_vl53l0x.VL53L0X(i2c)
# sensors["l0x_3"].set_address(0x29) # Changes default 0x29 to 0x32
# time.sleep(0.2)


def turnLeft(angle):
    print('hi')

def moveFwd(time):
    print('ho')


# proportional controller

target = 30
kp = 1.5
base_speed = 50


# while True:
#     try:
#         print(f"L0X 1: {sensors['l0x_1'].range} mm")
#         # print(f"L0X 2: {sensors['l0x_2'].range} mm")
#         # print(f"L0X 3: {sensors['l0x_3'].range} mm")

#         # greenexist = True
#         # redexist = False

#         if sensors['l5cx'].data_ready():

#             data = sensors['l5cx'].get_data()
#             distance_grid = np.array(data.distance_mm).reshape(8,8)
#             print(distance_grid[3][3])

#         else:
#             print("A",end=" ")

#         #     if (greenexist or redexist) and reading < 180:
#         #         turnLeft(45)
#         #         moveFwd(0.3)
#         #         turnLeft(45)
#         #     elif reading < 40:
#         #         turnLeft(90)

#         # error = target-sensors['l0x_1'].range
#         # correction = kp*error

#         # left_speed = base_speed-correction
#         # right_speed = base_speed+correction

#         # moveLeftFrontWheel(left_speed)
#         # moveLeftBackWheel(left_speed)
#         # moveRightFrontWheel(right_speed)
#         # moveRightBackWheel(right_speed)

#         # time.sleep(1)

#     except Exception as e:
#         print(f"Read error: {e}")
#     # time.sleep(0.5)