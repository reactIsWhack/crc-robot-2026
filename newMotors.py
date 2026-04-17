from gpiozero import OutputDevice, Device, PWMOutputDevice
import keyboard
from gpiozero.pins.lgpio import LGPIOFactory

Device.pin_factory = LGPIOFactory()

# left a corresponds to front left
left_a1 = 20
left_a2 = 16
left_pwm_a = 12

# left b corresponds to back left
left_b1 = 26
left_b2 = 19
left_pwm_b = 6

# right a corresponds to front right
right_a1 = 24
right_a2 = 25
right_pwm_a = 23

# right b corresponds to back right
right_b1 = 11
right_b2 = 9
right_pwm_b = 22

left_a1 = OutputDevice(20)
left_a2 = OutputDevice(16)
left_b1 = OutputDevice(26)
left_b2 = OutputDevice(19)

right_a1 = OutputDevice(24)
right_a2 = OutputDevice(25)
right_b1 = OutputDevice(11)
right_b2 = OutputDevice(9)

pwmBL = PWMOutputDevice(left_pwm_b)
pwmBR = PWMOutputDevice(right_pwm_b)
pwmFR = PWMOutputDevice(right_pwm_a)
pwmFL = PWMOutputDevice(left_pwm_a)

pwmBL.value = 0
pwmFL.value = 0
pwmFR.value = 0
pwmBR.value = 0

on = True
off = False

def moveFL(speed, direction):
    reverse = True
    if reverse:
        direction = "bwd" if direction == "fwd" else "fwd"
    if direction == "fwd":
        left_a1.on()
        left_a2.off()
    else:
        left_a1.off()
        left_a2.on()

    pwmFL.value = speed/100
    
def moveFR(speed, direction):
    reverse = True
    if reverse:
        direction = "bwd" if direction == "fwd" else "fwd"
    if direction == "fwd":
        right_a1.on()
        right_a2.off()
    else:
        right_a1.off()
        right_a2.on()
   
    pwmFR.value = speed/100
    
def moveBL(speed, direction):
    reverse = False
    if reverse:
        direction = "bwd" if direction == "fwd" else "fwd"
    if direction == "fwd":
        left_b1.on()
        left_b2.off()
    else:
        left_b1.off()
        left_b2.on()

    pwmBL.value = speed/100

def moveBR(speed, direction):
    reverse = False
    if reverse:
        direction = "bwd" if direction == "fwd" else "fwd"
    if direction == "fwd":
        right_b1.on()
        right_b2.off()
    else:
        right_b1.off()
        right_b2.on()

    pwmBR.value = speed/100

movement_speed = 45    
def moveRobotFwdOrBwd(direction):
    moveFL(movement_speed,direction)
    moveFR(movement_speed,direction)
    moveBL(movement_speed,direction)
    moveBR(movement_speed,direction)

def moveRobotRight():
    moveFL(movement_speed,"fwd")
    moveFR(movement_speed,"bwd")
    moveBL(movement_speed,"fwd")
    moveBR(movement_speed,"bwd")

def moveRobotLeft():
    moveFL(movement_speed,"bwd")
    moveBL(movement_speed,"bwd")
    moveFR(movement_speed,"fwd")
    moveBR(movement_speed,"fwd")

def stopRobot():
    moveFL(0,"stop")
    moveBL(0,"stop")
    moveFR(0,"stop")
    moveBR(0,"stop")

# try:
#     while True:
#         w_pressed = keyboard.is_pressed('w')
#         s_pressed = keyboard.is_pressed('s')
#         a_pressed = keyboard.is_pressed('a')
#         d_pressed = keyboard.is_pressed('d')
        
#         if not w_pressed and not s_pressed and not a_pressed and not d_pressed:
#             stopRobot()
            
        
#         if w_pressed:
#             moveRobotFwdOrBwd("fwd")
#         if s_pressed:
#             moveRobotFwdOrBwd("bwd")
#         if a_pressed:
#             moveRobotLeft()
#         if d_pressed:
#             moveRobotRight()
# finally:
#     Device.pin_factory.close()