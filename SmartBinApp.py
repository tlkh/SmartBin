# =============
# Configuration
# =============

import os
os.environ['KIVY_HOME'] = "/home/pi/.kivy"

config_path  = "data/config.json"
weights_path = "data/best_weights_11.h5"
frame_size = 1180, 1180 # Kivy resizes to this size before displaying the image

# ====================
# Initialise LED Strip
# ====================

print("[i] Initialising LED Strip")

from neopixel import *
from threading import Thread
import time

red = Color(0,255,0)
green = Color(255,0,0)
yellow = Color(255,255,0)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(25, 18, 800000, 10, False, 100, 0)
# Intialize the library (must be called once before other functions).
strip.begin()

class lightshow():
    """
    A thread that's sole purpose is to show you the loading progress.
    The model takes around 110 seconds to load, so that's what the progress bar shows you.
    """
    
    def __init__(self):
        global strip
        self.stopped = False
        self.start_time = None
        self.progress = 0
        self.pixels = strip.numPixels()

    def start(self):
        # start the thread to read frames from the video stream
        self.start_time = time.time()
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        global strip, yellow, green
        while True:
            if self.stopped:
                return
            elif self.progress == 100:
                self.stop()
            else:
                time.sleep(0.6)
                self.progress += 0.5
                for i in range(int( (self.progress+4.4)/100*self.pixels) ):
                    strip.setPixelColor(i, red)
                for i in range(int( (self.progress+2.6)/100*self.pixels) ):
                    strip.setPixelColor(i, yellow)
                for i in range(int(self.progress/100*self.pixels)):
                    strip.setPixelColor(i, green)
                strip.show()

    def stop(self):
        self.stopped = True

# ===========================
# Computer Vision Pipeline
#   Components (as threads):
#     1. Camera stream
#     2. Inference stream
# ===========================

progress_bar = lightshow().start()

print("[i] Initialising Computer Vision pipeline")
import cv2, json
import numpy as np
from box_utils import draw_boxes
from object_detection_model import ObjectDetection

with open(config_path) as config_buffer:    
    config = json.load(config_buffer)

from camera import PiVideoStream

print("[i] Loading feature extractor:", config['model']['backend'])
print("[+] Trained labels:", config['model']['labels'])
print("[i] Building model... This will take a while... (< 2 mins)")

load_start = time.time()

model = ObjectDetection(backend = config['model']['backend'],
            input_size          = config['model']['input_size'], 
            labels              = config['model']['labels'], 
            max_box_per_image   = config['model']['max_box_per_image'],
            anchors             = config['model']['anchors'])

print("[i] Model took", (time.time()-load_start), "seconds to load")

print("[c] Starting video capture")
cap = PiVideoStream().start()

print("[i] Loading weights from", weights_path)
model.load_weights(weights_path)

class predictions():
    """
    Streaming inferences independently of camera and UI updates
    Makes use of the following global variables:
      1. current frame from camera stream
      2. currently loaded object detection model
    """
    
    def __init__(self):
        self.boxes = ["can", "bottle", "ken", "grace", "frank", "tim", "shelly"]
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        global model, frame
        # keep looping infinitely until the thread is stopped
        while True:
            if self.stopped:
                return
            else:
                self.boxes = model.predict(frame)

    def read(self):
        return self.boxes

    def stop(self):
        self.stopped = True

# =========
# IOT Setup
# =========

from iot import *

firebase = firebase_setup()
firebase_reset(firebase)

# ======================================================
# Perform one inference to test if everything is working
# ======================================================

print("[i] Running self-test")
try:
    frame = cap.read() # read one frame from the stream
    boxes = model.predict(frame) # get bounding boxes
    # if previous line succeded, our model is functional123start the predictions stream
    pred = predictions().start()
    print("[+] Self-test: OK")
except Exception as error:
    print("[!] Fatal error", end=": ")
    print(error)
    exit()

# ==============================
# Kivy Configuration
#   Only needed on the first run
# ==============================

from kivy.config import Config
Config.set('graphics', 'fullscreen', 'fake')
Config.set('graphics', 'fbo', 'hardware')
Config.set('graphics', 'show_cursor', 1)
Config.set('graphics', 'borderless', 0)
Config.set('kivy', 'exit_on_escape', 1)
Config.write()

# =========
# GUI Setup
# =========

from kivy.app import App
from kivy.graphics import *
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

Builder.load_file('app_layout.kv') # Kivy layout file

# Declare individual screens
class MainView(Screen):
    """Main screen with camera feed and 3 buttons"""
    
    def __init__(self, **kwargs):
        global cap, frame, frame_size
        
        # capture and render the first frame
        self.frame_size = frame_size
        frame = cap.read()
        image = cv2.flip(frame,0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, frame_size)
        buf = image.tostring()
        self.image_texture = Texture.create(size=( image.shape[1], image.shape[0]), colorfmt='rgb')
        self.image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

        # create keyboard bindings
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        # coordinates of Trashy
        self.t_x = 0
        self.t_y = 0

        self.current_user = 'No user yet'
        self.labels = ["can", "bottle", "ken", "grace", "frank", "tim", "shelly"]
        self.users = ["ken", "grace", "frank", "tim", "shelly"]

        super(MainView,self).__init__(**kwargs)
        Clock.schedule_interval(self.tick,0.06)
        
    def tick(self, dt):
        global pred, cap, frame, strip, red, green, firebase

        can_detected, bottle_detected = False, False

        frame = cap.read()
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = pred.read()
        image = draw_boxes(image, boxes, config['model']['labels'])
        image = cv2.resize(cv2.flip(image,0), self.frame_size)
        buf = image.tostring()
        self.image_texture = Texture.create(size=(self.frame_size), colorfmt='rgb')
        self.image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self.ids.cameraView.texture = self.image_texture
        
        if len(boxes) > 0:
            self.t_x = int((boxes[0].xmin-0.5) * 1000) - 80
            self.t_y = -1 * (int((boxes[0].ymin-0.5) * 1000) + 80)
            self.ids.trashyView.opacity = 1.0
            self.ids.trashyView.pos = (self.t_x, self.t_y)
            display_label = ""
            for box in boxes:
                curr_label = box.get_label()
                if self.labels[curr_label] == "can":
                    can_detected = True
                if self.labels[curr_label] == "bottle":
                    bottle_detected = True
                if self.labels[curr_label] in self.users:
                    self.current_user = self.labels[curr_label]
            if can_detected == True:
                for i in range(8):
                    strip.setPixelColor(i, red)
                for i in range(15,25):
                    strip.setPixelColor(i, green)
                display_label = display_label + "\nThrow your can in the recycling bin\nPlease wash the can first!"
                if self.current_user in self.users:
                    firebase_update(firebase, self.current_user, 'cans', 1)
            if bottle_detected == True:
                for i in range(8):
                    strip.setPixelColor(i, red)
                for i in range(8,15):
                    strip.setPixelColor(i, green)
                display_label = display_label + "\nThrow your bottle into the recycling bin\nPlease empty it first!"
                if self.current_user in self.users:
                    firebase_update(firebase, self.current_user, 'bottles', 1)
            self.ids.labelObjDet.text = display_label
        else:
            self.ids.trashyView.opacity = 0.0
            self.ids.labelObjDet.text = "No recyclable trash detected"
        strip.show()
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, red)
        for i in range(8):
            strip.setPixelColor(i, green)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        global strip
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, green)
        strip.show()
        global sm
        if keycode[1] == '1':
            sm.current = 'infoView'
        elif keycode[1] == '2':
            sm.current = 'aboutView'
        elif keycode[1] == '3':
            self.quit()
        return True

    def quit(self):
        global strip
        pred.stop()
        cap.stop()
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0,0,0))
        strip.show()
        Window.close()
        App.get_running_app().stop()
        exit()

class InfoView(Screen):
    """Secondary screen that displays information about recycling in Singapore"""
    
    def __init__(self, **kwargs):
        super(InfoView,self).__init__(**kwargs)
        # create keyboard bindings
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        global sm
        if keycode[1] == 'a':
            sm.current = 'mainView'
        return True

class AboutView(Screen):
    """Secondary screen that displays information about this project"""
    
    def __init__(self, **kwargs):
        super(AboutView,self).__init__(**kwargs)
        # create keyboard bindings
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        global sm
        if keycode[1] == 'a':
            sm.current = 'mainView'
        return True

# ==========================================
# Tie everything together and launch the app
# ==========================================

# everything works! set LED strip to initial state
for i in range(strip.numPixels()):
    strip.setPixelColor(i, red)
for i in range(8):
    strip.setPixelColor(i, green)
strip.show()

print("[u] Loading UI")
Window.clearcolor = (1, 1, 1, 1) # set white background

# setup Kivy screen manager
sm = ScreenManager()
sm.add_widget(MainView(name='mainView'))
sm.add_widget(InfoView(name='infoView'))
sm.add_widget(AboutView(name='aboutView'))

class SmartBinApp(App):
    def build(self):
        return sm
    
try:
    SmartBinApp().run()
except KeyboardInterrupt:
    pred.stop()
    cap.stop()
    print('exciting due to KeyboardInterrupt')
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0,0,0))
    strip.show()
    App.get_running_app().stop()
    exit()
