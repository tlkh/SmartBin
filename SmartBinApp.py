# computer vision pipeline modules
import numpy as np
#from preprocessing import parse_annotation
#from utils import draw_boxes
#from frontend import YOLO
from threading import Thread
import cv2, json, time

# GUI modules

from kivy.config import Config
Config.set('graphics', 'fullscreen', 'fake')
Config.set('graphics', 'fbo', 'software')
Config.set('graphics', 'show_cursor', 1)
Config.set('graphics', 'borderless', 0)
Config.set('kivy', 'exit_on_escape', 1)
Config.write()

from kivy.app import App
from kivy.graphics import *
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix import rst
from kivy.core.window import Window

# ========================
# Computer Vision Pipeline
# ========================

#from camera import PiVideoStream
#
#cv2.namedWindow('image', cv2.WINDOW_NORMAL)
#cv2.resizeWindow('image', 640, 480)

class predictions():
    """Streaming inferences independently of camera and UI updates"""
    
    def __init__(self):
        self.boxes = ["can", "bottle"]
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        #global yolo
        #global frame
        # keep looping infinitely until the thread is stopped
        while True:
            if self.stopped:
                return
            else:
                pass
                #pred_start = time.time()
                #self.boxes = yolo.predict(frame)
                #print(round(1/(time.time() - pred_start), 3), "FPS")

    def read(self):
        return self.boxes

    def stop(self):
        self.stopped = True

# ===========
# GUI Classes
# ===========

Builder.load_file('app_layout.kv') # Kivy layout file

# Declare individual screens
class MainView(Screen):
    """Main screen with camera feed and 3 buttons"""
    
    def __init__(self, **kwargs):
        super(MainView,self).__init__(**kwargs)
        Clock.schedule_interval(self.tick,0.03334)
        self.objects_detected = None
        self.start_time = time.time()
        with self.canvas:
            self.rect = Rectangle(pos=(10, 10), size=(500, 500), source='img/placeholder.jpg')

    # future reference (OpenCV):
    # https://gist.github.com/ExpandOcean/de261e66949009f44ad2

    def tick(self, dt):
        global pred
        #global cap
        #frame = cap.read()
        #boxes = pred.read()
        #frame = draw_boxes(frame, boxes, config['model']['labels'])
        #cv2.imshow('image',frame)
        #cv2.waitKey(1)
        objects_detected_label = str(pred.read())
        self.ids.labelObjDet.text = objects_detected_label + " " + str(round(time.time()-self.start_time,2))

    def on_quit(self):
        Window.close()
        App.get_running_app().stop()
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

# start capturing and streaming from camera
#cap = PiVideoStream().start()

# setup Kivy screen manager
sm = ScreenManager()
sm.add_widget(MainView(name='mainView'))
sm.add_widget(InfoView(name='infoView'))
sm.add_widget(HelpView(name='helpView'))
sm.add_widget(AboutView(name='aboutView'))

# begin streaming predictions
pred = predictions().start()

class SmartBinApp(App):
    def build(self):
        return sm
    
try:
    SmartBinApp().run()
except KeyboardInterrupt:
    App.get_running_app().stop()
    print('exciting due to Keyboard')
    exit()
