from gpiozero import OutputDevice, Device, PWMOutputDevice
import keyboard
from gpiozero.pins.lgpio import LGPIOFactory

Device.pin_factory = LGPIOFactory()

# left a corresponds to front left
left_a1_pin = 20
left_a2_pin = 16
left_pwm_a = 12

# left b corresponds to back left
left_b1_pin = 26
left_b2_pin = 19
left_pwm_b = 6

# right a corresponds to front right
right_a1_pin = 24
right_a2_pin = 25
right_pwm_a = 23

# right b corresponds to back right
right_b1_pin = 5 #5 #9
right_b2_pin = 13 #13 #11
right_pwm_b = 17 #17 #22

left_a1 = OutputDevice(left_a1_pin)
left_a2 = OutputDevice(left_a2_pin)
left_b1 = OutputDevice(left_b1_pin)
left_b2 = OutputDevice(left_b2_pin)

right_a1 = OutputDevice(right_a1_pin)
right_a2 = OutputDevice(right_a2_pin)
right_b1 = OutputDevice(right_b1_pin)
right_b2 = OutputDevice(right_b2_pin)

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
    reverse = False
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
    reverse = True
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

def moveRobotFwdOrBwd(speed, direction):
    moveFL(speed,direction)
    moveFR(speed,direction)
    moveBL(speed,direction)
    moveBR(speed,direction)

def moveRobotRight(speed):
    moveFL(speed,"fwd")
    moveFR(speed,"bwd")
    moveBL(speed,"fwd")
    moveBR(speed,"bwd")

def moveRobotLeft(speed):
    moveFL(speed,"bwd")
    moveFR(speed,"fwd")
    moveBL(speed,"bwd")
    moveBR(speed,"fwd")

def stopRobot():
    moveFL(0,"stop")
    moveBL(0,"stop")
    moveFR(0,"stop")
    moveBR(0,"stop")