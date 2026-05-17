import keyboard
from clawFunctions import openClawHands, closeClawHands, liftClaw, moveClawDown, openDoor, closeDoor

try:
    while True:

        w_pressed = keyboard.is_pressed('w')
        s_pressed = keyboard.is_pressed('s')
        a_pressed = keyboard.is_pressed('a')
        d_pressed = keyboard.is_pressed('d')
        
        if w_pressed:
            liftClaw()
        elif s_pressed:
            moveClawDown()
        elif a_pressed:
            openClawHands()
        elif d_pressed:
            closeClawHands()
        elif keyboard.is_pressed('o'):
            openDoor()
        elif keyboard.is_pressed('c'):
            closeDoor()
        # kit.servo[door].angle = angle
        # kit.servo[lift_servo_right].angle = angle
        # kit.servo[lift_servo_left].angle = 180-angle
        # kit.servo[claw_servo_right].angle = angle
        # kit.servo[claw_servo_left].angle = 180-angle
except KeyboardInterrupt:
    print("done")