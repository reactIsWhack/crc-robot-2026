import board
import neopixel

pixel_pin = board.D18
num_pixels = 8

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.4)

def turnLedOn():
    for i in range(0, num_pixels):
        pixels[i] = (90,60,25)

def turnLedOff():
    for i in range(0, num_pixels):
        pixels[i] = (0, 0, 0)