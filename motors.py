import evdev
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

device = evdev.InputDevice('/dev/input/event11')

driverL_motorF_in1 = 6
driverL_motorF_in2 = 5
driverL_motorB_in1 = 19
driverL_motorB_in2 = 13

driverR_motorF_in1 = 25
driverR_motorF_in2 = 12
driverR_motorB_in1 = 16
driverR_motorB_in2 = 20

driverL_enbF = 22
driverL_enbB = 26
driverR_enbF = 24
driverR_enbB = 21

GPIO.setup(driverL_motorF_in1,GPIO.OUT)
GPIO.setup(driverL_motorF_in2,GPIO.OUT)
GPIO.setup(driverL_motorB_in1,GPIO.OUT)
GPIO.setup(driverL_motorB_in2,GPIO.OUT)

GPIO.setup(driverR_motorF_in1,GPIO.OUT)
GPIO.setup(driverR_motorF_in2,GPIO.OUT)
GPIO.setup(driverR_motorB_in1,GPIO.OUT)
GPIO.setup(driverR_motorB_in2,GPIO.OUT)

GPIO.setup(driverL_enbF,GPIO.OUT)
GPIO.setup(driverL_enbB,GPIO.OUT)
GPIO.setup(driverR_enbF,GPIO.OUT)
GPIO.setup(driverR_enbB,GPIO.OUT)

driverL_enbF_pwm = GPIO.PWM(driverL_enbF,100)
driverL_enbB_pwm = GPIO.PWM(driverL_enbB,100)
driverR_enbF_pwm = GPIO.PWM(driverR_enbF,100)
driverR_enbB_pwm = GPIO.PWM(driverR_enbB,100)

driverL_enbF_pwm.start(0)
driverL_enbB_pwm.start(0)
driverR_enbF_pwm.start(0)
driverR_enbB_pwm.start(0)

def moveLF(speed = 0,direction = "clockwise"):
    GPIO.output(driverL_motorF_in1,True if direction == "clockwise" else False)
    GPIO.output(driverL_motorF_in2,False if direction == "clockwise" else True)
    driverL_enbF_pwm.ChangeDutyCycle(speed)
    
def moveLB(speed = 0,direction = "clockwise"):
    GPIO.output(driverL_motorB_in1,True if direction == "clockwise" else False)
    GPIO.output(driverL_motorB_in2,False if direction == "clockwise" else True)
    driverL_enbB_pwm.ChangeDutyCycle(speed)
    
def moveRF(speed = 0,direction = "clockwise"):
    GPIO.output(driverR_motorF_in1,False if direction == "clockwise" else True)
    GPIO.output(driverR_motorF_in2,True if direction == "clockwise" else False)
    driverR_enbF_pwm.ChangeDutyCycle(speed)
    
def moveRB(speed = 0,direction = "clockwise"):
    GPIO.output(driverR_motorB_in1,False if direction == "clockwise" else True)
    GPIO.output(driverR_motorB_in2,True if direction == "clockwise" else False)
    driverR_enbB_pwm.ChangeDutyCycle(speed)


try:
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_ABS:
            if event.code == evdev.ecodes.ABS_Y:
                if abs(event.value) > 1000:
                    speed = abs(event.value)/32750*100
                    speed = min(100,max(0,speed))
                    moveLF(speed,"clockwise" if event.value > 0 else "backward")
                    moveLB(speed,"clockwise" if event.value > 0 else "backward")
                else:
                    moveLF()
                    moveLB()

finally:
    GPIO.cleanup()
