import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

Builder.load_string("""
<MainView>
    spacing:10
    padding:20
    GridLayout:
        cols:2
        GridLayout:
            rows:2
            canvas:
                id:cameraCanvas
                Color:
                    rgb: 1, 1, 1
                Rectangle:
                    source: 'sample/placeholder.jpg'
                    size: self.size
            Label:
                size_hint_y: None
                height: 100
                font_size:30
                text:'{{object}} DETECTED'
        GridLayout:
            rows:3
            width: 250
            size_hint_x: None
            Button:
                text: 'Recycling in Singapore'
            Button:
                text: 'Help me!'
                on_press:
                    root.manager.transition.direction = 'left'
                    root.manager.current = 'helpView'
            Button:
                text: "What's this about?"
<HelpView>
    BoxLayout:
        Button:
            text: 'Find Out More'
        Button:
            text: 'Back to Main Screen'
            
            on_press:
                root.manager.transition.direction = 'right'
                root.manager.current = 'mainView'
""")

# Declare both screens
class MainView(Screen):
    pass

class HelpView(Screen):
    pass

# Create the screen manager
sm = ScreenManager()
sm.add_widget(MainView(name='mainView'))
sm.add_widget(HelpView(name='helpView'))

class SmartBinApp(App):

    def build(self):
        return sm

if __name__ == '__main__':
    SmartBinApp().run()
