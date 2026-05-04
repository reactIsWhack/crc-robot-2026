from adafruit_servokit import ServoKit
kit = ServoKit(channels=16)

lift_servo_left = 9
lift_servo_right = 8
claw_servo_right = 11 # 3 = open, 180 = closed
claw_servo_left = 10 # 180 = open, 0 = closed

try:
    while True:
        angle = int(input("Enter an angle: "))

        # kit.servo[lift_servo_left].angle = angle
        kit.servo[lift_servo_left].angle = angle
        # kit.servo[claw_servo_right].angle = angle
        # kit.servo[claw_servo_left].angle = angle
except KeyboardInterrupt:
    print("done")
