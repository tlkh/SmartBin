from neopixel import *

strip = Adafruit_NeoPixel(30, 18, 800000, 10, False, 100, 0)
strip.begin()

red = Color(255,0,0)
green=Color(0,255,0)

for i in range(strip.numPixels()):
    strip.setPixelColor(i, red)
for i in range(9):
    strip.setPixelColor(i, green)


strip.show()
