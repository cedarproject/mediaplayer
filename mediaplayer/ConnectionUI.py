from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

from .Settings import settings

class ConnectionUI(GridLayout):
    cols = 2
    
    def __init__(self, mediaplayer, **kwargs):
        super(ConnectionUI, self).__init__(**kwargs)
        
        self.mediaplayer = mediaplayer

    def go(self):
        if self.mediaplayer.config.get('connection', 'autoconnect') == 'yes':
            self.do_connect(None, auto = True)
        else:
            self.do_connect_ui()

    def do_connect_ui(self, error = ''):
        self.clear_widgets()
        
        self.server_input = TextInput(text = self.mediaplayer.config.get('connection', 'server'), **settings.widget_defaults)
        self.server_button = Button(text = 'Connect', size_hint = (0.25, 1), **settings.widget_defaults)
        self.server_button.bind(on_press = self.do_connect)
        
        self.add_widget(self.server_input)
        self.add_widget(self.server_button)
        
        self.add_widget(Label(text = error, color = (1, 0, 0, 1), **settings.widget_defaults))
    
    def do_connect(self, button, auto = False):
        self.clear_widgets()
        
        if auto:
            connecting = self.mediaplayer.connect(self.mediaplayer.config.get('connection', 'server'))
        else:
            connecting = self.mediaplayer.connect(self.server_input.text)
        
        if connecting: self.do_loading_ui()
    
    def do_loading_ui(self):
        self.clear_widgets()
        
        self.add_widget(Label(text = 'Connecting...', font_name = settings.font, font_size = settings.font_size * 2))
