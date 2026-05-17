
import cv2
import numpy as np
from collections import namedtuple
from picamera2 import Picamera2
from ultralytics import YOLO



identifiedVictim = namedtuple('identifiedVictim', ['x', 'y', 'perimeter', 'color'])



# returns the closest object
def get_closest_object(frame, model, confidence_threshold=0.25, show_window=True):
    
    closest_target = None
    max_perimeter = -1
    
    results = model(frame, stream=True, conf=confidence_threshold)
    
    # deep copy for display
    display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if show_window else None
    
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        clss = result.boxes.cls.cpu().numpy()
        
        for box, cls in zip(boxes, clss):
            x1, y1, x2, y2 = map(int, box)
            
            # Map numeric class IDs to your color strings
            class_id = int(cls)
            color_name = "black" if class_id == 0 else "silver" if class_id == 1 else "unknown"

            # Dimensions and spatial tracking math
            width = x2 - x1
            height = y2 - y1
            center_x = int(x1 + (width / 2))
            center_y = int(y1 + (height / 2))
            perimeter = 2 * (width + height)
            
            # Build current target namedtuple
            current_target = identifiedVictim(x=center_x, y=center_y, perimeter=perimeter, color=color_name)
            
            # Tracking check: Is this object closer than previous ones?
            if perimeter > max_perimeter:
                max_perimeter = perimeter
                closest_target = current_target

            # Draw everything on the frame if window output is turned on
            if show_window:
                box_color = (0, 0, 255) if color_name == "black" else (0, 255, 0)
                # Outer rectangle box
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), box_color, 2)
                # Center point dot
                cv2.circle(display_frame, (center_x, center_y), 5, (0, 255, 0), -1)
                # Text specs label
                label = f"{color_name.upper()} (P:{perimeter}px)"
                cv2.putText(display_frame, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

    # Render window frame externally if activated
    if show_window:
        # Highlight the tracked target on frame if one exists
        if closest_target:
            cv2.putText(display_frame, "► TRACKING CLOSEST ◄", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
        cv2.imshow("Robot Tracking Stream", display_frame)
        cv2.waitKey(1)  # Must call waitKey to refresh the window system UI thread

    return closest_target






##########################################
# Loop
##########################################

### Camera ###
picam2 = Picamera2(1)
config = picam2.create_preview_configuration(main={"format":"BGR888", "size":(640,640)},transform=Transform(hflip=1, vflip=1))
picam2.start(config)




### State ###

state = "Looking"
lookingfor = "Silver1" # Silver2 and Black

'''
Looking --> *Found* --> Adjust --> *In position* --> Pick up --> Repeat for Silver2 -->

Find green area --> Adjust --> Drop off victims --> Looking

'''





model = YOLO("/home/firstenergyrobot/CRC/best_ncnn_model")

try:
    while True:
        frame = picam2.capture_array()
        frame = np.flipud(frame)
        
        # Call tracking function (now returns either one namedtuple or None)
        target = get_closest_object(frame, model, confidence_threshold=0.30, show_window=True)
        
        if target:
            print(f"Targeting closest item -> Color: {target.color} | X: {target.x} | Size: {target.perimeter}")

            if target.perimeter > 400 and target.color == "Silver" and target.x > 200 and target.x < 400:
                print("############# SUCCESS #####################")
                raise KeyboardInterrupt
            
        else:
            print("Searching for objects...")




except KeyboardInterrupt:
    print("\nShutting down system...")
finally:
    picam2.stop()
    cv2.destroyAllWindows()
