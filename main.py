import os
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0' # Tells SDL2 not to hide the window when unfocused while fullscreen.

import kivy
kivy.require('1.9.0')

import kivy.utils

from kivy.config import Config
Config.set('kivy', 'log_level', 'debug')

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import Color, Rectangle

import sys
import json
import time

from MeteorClient import MeteorClient

class MediaPlayer(App):
    def __init__(self, **kwargs):
        self.server = None
        self.ready = False

        self.state = 'disconnected' # 'disconnected' => 'connecting' => 'loading' => 'connected'
        self.binds = {}
        
        self.fullscreen = False
        
        super(MediaPlayer, self).__init__(**kwargs)
        
    def connect(self, server):
        self.server = server
        
        self.meteor = MeteorClient('ws://{}/websocket'.format(self.server))
        self.meteor.on('connected', self.connected)
        self.meteor.connect()

        self.state = 'connecting'
        
    def connected(self):
        self.state = 'loading'
        
        self.collections_ready = 0
        self.meteor.subscribe('media', callback=self.subscription_ready)
        self.meteor.subscribe('mediaplaylists', callback=self.subscription_ready)

    def subscription_ready(self, err):
        if err: print(err)
        self.collections_ready += 1

        if self.collections_ready == 2:
            self.state = 'connected'

    def get_application_config(self):
        return super(MediaPlayer, self).get_application_config('~/.%(appname)s.ini')

    def build_config(self, config):
        config.setdefaults('connection', {
            'servers': '',
        })
   
    def toggle_fullscreen(self, thing, touch):        
        if not self.ui.layout.collide_point(*touch.pos):
            if self.fullscreen: Window.fullscreen = 0
            else: Window.fullscreen = 'auto'
            self.fullscreen = not self.fullscreen
        
    def build(self):
        self.title = 'Cedar Media Player'

# TODO make icon!        
#        if kivy.utils.platform is 'windows':
#            self.icon = 'logo/logo-128x128.png'
#        else:
#            self.icon = 'logo/logo-1024x1024.png'

        self.layout = FloatLayout()
        self.layout.add_widget(self.source)
                
        self.ui = UserInterface(self)
        
        return self.layout

