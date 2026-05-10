from newMotors import moveRobotFwdOrBwd, stopRobot, moveRobotLeft, moveRobotRight
import keyboard

base_speed = 50

try:
    while True:
        w_pressed = keyboard.is_pressed('w')
        s_pressed = keyboard.is_pressed('s')
        a_pressed = keyboard.is_pressed('a')
        d_pressed = keyboard.is_pressed('d')
        
        if not w_pressed and not s_pressed and not a_pressed and not d_pressed:
            stopRobot()
            
        
        if w_pressed:
            moveRobotFwdOrBwd(base_speed,"fwd")
        if s_pressed:
            moveRobotFwdOrBwd(base_speed,"bwd")
        if a_pressed:
            moveRobotLeft(base_speed)
        if d_pressed:
            moveRobotRight(base_speed)
except KeyboardInterrupt:
    print("done")