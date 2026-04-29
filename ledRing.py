import board
import neopixel
import time

pixel_pin = board.D21
num_pixels = 8

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1)

def turnLedOn(red, green, blue):
    for i in range(0, num_pixels):
        pixels[i] = (red, green, blue)

def turnLedOff():
    for i in range(0, num_pixels):
        pixels[i] = (0, 0, 0)


# turnLedOn(255, 0, 0)
# time.sleep(2)
# turnLedOn(0, 255, 0)
# time.sleep(2)
# turnLedOn(0, 0, 255)
# time.sleep(2)
# turnLedOff()
