from tkinter import *
import math
import cv2

# width = 800, height = 480 for monitor

class Popup:
    def __init__(self):
        self.window = Tk()
        self.button_width = 105
        self.button_height = 30
        self.window_width = 700
        self.window_height = 400
        self.window.resizable(False, False) # make window unable to be resized

        self.redIncButton = Button(self.window, text="Red Increase")
        self.redDecButton = Button(self.window, text="Red Decrease")
        self.blueIncButton = Button(self.window, text="Blue Increase")
        self.blueDecButton = Button(self.window, text="Blue Decrease")
        self.greenIncButton = Button(self.window, text="Green Increase")
        self.greenDecButton = Button(self.window, text="Green Decrease")
        self.coarseButton = Button(self.window, text="Mode: Coarse")
        self.buttons = [self.redIncButton, self.redDecButton, self.blueIncButton, self.blueDecButton, self.greenIncButton, self.greenDecButton]
        
        self.red = 255
        self.blue = 130
        self.green = 255
        self.coarse = True
        self.changeAmnt = 25
        self.red_label = Label(self.window, text=f"r: {self.red}",)
        self.green_label = Label(self.window, text=f"g: {self.green}")
        self.blue_label = Label(self.window, text=f"b: {self.blue}")

        self.start_x = 10
        self.start_y = 10
        self.vertical_dist = 50

        # BIG START BUTTON
        self.startButton = Button(
            self.window,
            text="START",
            font=("Arial", 24, "bold"),
            bg="green",
            fg="white",
        )
    
    def decRed(self):
        self.red = max(0, self.red-self.changeAmnt)
        self.updateRGBLabels()
    def incRed(self):
        self.red = min(255, self.red+self.changeAmnt)
        self.updateRGBLabels()
    def decBlue(self):
        self.blue = max(0, self.blue-self.changeAmnt)
        self.updateRGBLabels()
    def incBlue(self):
        self.blue = min(255, self.blue+self.changeAmnt)
        self.updateRGBLabels()
    def decGreen(self):
        self.green = max(0, self.green-self.changeAmnt)
        self.updateRGBLabels()
    def incGreen(self):
        self.green = min(255, self.green+self.changeAmnt)
        self.updateRGBLabels()
    
    def switchMode(self):
        self.coarse = False if self.coarse else True
        if self.coarse:
            self.changeAmnt = 25
            self.coarseButton.config(text="Mode: Coarse")
        else:
            self.changeAmnt = 2
            self.coarseButton.config(text="Mode: Fine")
    
    def createButtons(self):
        self.window.geometry(f"{self.window_width}x{self.window_height}")

        spacing = self.button_width + ((self.window_width - 2 * self.start_x) - (6 * self.button_width)) / 5
        for i, button in enumerate(self.buttons):
            button.place(x=self.start_x + spacing * i, y=self.start_y, width=self.button_width, height=self.button_height)

        # PLACE BIG START BUTTON IN CENTER
        self.startButton.place(
            x=self.window_width / 2 - 300,
            y=self.window_height / 2 - 100,
            width=400,
            height=200
        )
        self.coarseButton.place(x=(self.window_width/2 - self.button_width/2), y=self.start_y+self.vertical_dist)
        self.redDecButton.config(command=self.decRed)
        self.redIncButton.config(command=self.incRed)
        self.blueDecButton.config(command=self.decBlue)
        self.blueIncButton.config(command=self.incBlue)
        self.greenDecButton.config(command=self.decGreen)
        self.greenIncButton.config(command=self.incGreen)
        self.coarseButton.config(command=self.switchMode)
        self.startButton.config(command=self.startLineFollowing)
    
    def createRGBLabels(self):
        text_spacing = 100
        
        self.red_label.place(x=self.start_x, y=self.start_y+self.vertical_dist)
        self.blue_label.place(x=self.start_x+text_spacing, y=self.start_y+self.vertical_dist)
        self.green_label.place(x=self.start_x+text_spacing*2, y=self.start_y+self.vertical_dist)

    def updateRGBLabels(self):
        self.red_label.config(text=f"r: {self.red}")
        self.blue_label.config(text=f"b: {self.blue}")
        self.green_label.config(text=f"g: {self.green}")
    
    def display_window(self):
        self.window.mainloop()

    def startLineFollowing(self):
        self.window.destroy()
        cv2.destroyAllWindows()

    