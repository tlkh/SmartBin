# =============
# Configuration
# =============

config_path  = "data/config.json"
weights_path = "data/best_weights8.h5"
frame_size = 1180, 1180 # Kivy resizes to this size before displaying the image

# ===========================
# Computer Vision Pipeline
#   Components (as threads):
#     1. Camera stream
#     2. Inference stream
# ===========================

print("[i] Initialising Computer Vision pipeline")
import cv2, json, time
import numpy as np
from box_utils import draw_boxes
from object_detection_model import ObjectDetection
from threading import Thread

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
        self.boxes = ["can", "bottle"]
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

print("[i] Running self-test")
try:
    frame = cap.read()
    boxes = model.predict(frame)
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
from kivy.uix import rst
from kivy.core.window import Window

Builder.load_file('app_layout.kv') # Kivy layout file

# Declare individual screens
class MainView(Screen):
    """Main screen with camera feed and 3 buttons"""
    
    def __init__(self, **kwargs):
        global cap, frame, frame_size
        self.frame_size = frame_size
        frame = cap.read()
        image = cv2.flip(frame,0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, frame_size)
        buf = image.tostring()
        self.image_texture = Texture.create(size=( image.shape[1], image.shape[0]), colorfmt='rgb')
        self.image_texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        super(MainView,self).__init__(**kwargs)
        self.t_x = 0
        self.t_y = 0
        self.labels = ["can", "bottle"]
        Clock.schedule_interval(self.tick,0.06)
        self.start_time = time.time()

    def tick(self, dt):
        global pred, cap, frame
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
        objects_detected_label = []
        
        if len(boxes) > 0:
            self.t_x = int((boxes[0].xmin-0.5) * 1000) - 80
            self.t_y = -1 * (int((boxes[0].ymin-0.5) * 1000) + 80)
            self.ids.trashyView.opacity = 1.0
            self.ids.trashyView.pos = (self.t_x, self.t_y)
            display_label = ""
            for box in boxes:
                if self.labels[box.get_label()] == "can":
                    can_detected = True
                if self.labels[box.get_label()] == "bottle":
                    bottle_detected = True
            if can_detected == True:
                display_label = display_label + "\nThrow your can in the recycling bin\nPlease wash the can first!" 
            if bottle_detected == True:
                display_label = display_label + "\nThrow your bottle into the recycling bin\nPlease empty it first!"
            self.ids.labelObjDet.text = display_label
        else:
            self.ids.trashyView.opacity = 0.0
            self.ids.labelObjDet.text = "No recyclable trash detected"

    def on_quit(self):
        Window.close()
        App.get_running_app().stop()
        pred.stop()
        cap.stop()
        exit()

class InfoView(Screen):
    """Secondary screen that displays information about recycling in Singapore"""
    
    def __init__(self, **kwargs):
        super(InfoView,self).__init__(**kwargs)

class HelpView(Screen):
    """Secondary screen that assists the user"""
    
    def __init__(self, **kwargs):
        super(HelpView,self).__init__(**kwargs)

class AboutView(Screen):
    """Secondary screen that displays information about this project"""
    
    def __init__(self, **kwargs):
        super(AboutView,self).__init__(**kwargs)

# ==========================================
# Tie everything together and launch the app
# ==========================================

print("[u] Loading UI")

# setup Kivy screen manager
sm = ScreenManager()
sm.add_widget(MainView(name='mainView'))
sm.add_widget(InfoView(name='infoView'))
sm.add_widget(HelpView(name='helpView'))
sm.add_widget(AboutView(name='aboutView'))

class SmartBinApp(App):
    def build(self):
        return sm
    
try:
    SmartBinApp().run()
except KeyboardInterrupt:
    print('exciting due to KeyboardInterrupt')
    App.get_running_app().stop()
    pred.stop()
    cap.stop()
    exit()
