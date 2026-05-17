from adafruit_servokit import ServoKit
kit = ServoKit(channels=16)

lift_servo_left = 9
lift_servo_right = 8
claw_servo_right = 13 # 3 = open, 180 = closed
claw_servo_left = 12 # 180 = open, 0 = closed
door = 0 # range = [1, 110]

kit.servo[lift_servo_left].set_pulse_width_range(500, 2500)
kit.servo[lift_servo_right].set_pulse_width_range(500, 2500)
kit.servo[claw_servo_left].set_pulse_width_range(500, 2500)
kit.servo[claw_servo_right].set_pulse_width_range(500, 2500)
kit.servo[door].set_pulse_width_range(500, 2500)

def liftClaw(desiredAngle=179):
    kit.servo[lift_servo_right].angle = desiredAngle
    kit.servo[lift_servo_left].angle = 180-desiredAngle  

def moveClawDown(desiredAngle=25):
    kit.servo[lift_servo_right].angle = desiredAngle
    kit.servo[lift_servo_left].angle = 180-desiredAngle  

# open = 1 deg, close = 120 deg
def openClawHands(angle=140):
    kit.servo[claw_servo_right].angle = 180-angle
    kit.servo[claw_servo_left].angle = angle

def closeClawHands(angle=110):
    kit.servo[claw_servo_right].angle = angle
    kit.servo[claw_servo_left].angle = 180-angle

def openDoor():
    kit.servo[door].angle = 110

def closeDoor():
    kit.servo[door].angle = 1
