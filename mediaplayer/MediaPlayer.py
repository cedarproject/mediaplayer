import os
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0' # Tells SDL2 not to hide the window when unfocused while fullscreen.

import kivy
kivy.require('1.9.0')

import kivy.utils

from kivy.config import Config
Config.set('kivy', 'log_level', 'debug')
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('graphics', 'window_state', 'maximized')

from kivy.app import App
from kivy.metrics import cm
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

import sys
import json
import time

from MeteorClient import MeteorClient

from .MenuBar import MenuBar
from .ConnectionUI import ConnectionUI
from .PlaylistSelectPane import PlaylistSelectPane
from .PlaylistContentPane import PlaylistContentPane
from .VideoPlayer import CMPVideoPlayer as VideoPlayer

class MediaPlayer(App):
    def __init__(self, **kwargs):
        self.server = None
        self.ready = False

        self.state = 'disconnected' # 'disconnected' => 'connecting' => 'loading' => 'connected'
        self.binds = {}
        
        self.shuffle = False
        self.current_playlist = 'special_all_media'
        
        super(MediaPlayer, self).__init__(**kwargs)
        
    def connect(self, server):
        self.server = server

        self.meteor = MeteorClient('ws://{}/websocket'.format(self.server))

        self.meteor.on('added', self.added)
        self.meteor.on('changed', self.changed)
        self.meteor.on('removed', self.removed)
        self.meteor.on('connected', self.connected)

        try:
            self.meteor.connect()
        except Exception as e:
            self.connectionui.do_connect_ui(error = repr(e))
            return False

        self.build_main_ui()

        self.state = 'connecting'
        
        return True
        
    def connected(self):
        self.config.set('connection', 'server', self.server)
        self.config.write()

        self.state = 'loading'
        
        self.collections_ready = 0
        self.meteor.subscribe('media', callback=self.subscription_ready)
        self.meteor.subscribe('mediaplaylists', callback=self.subscription_ready)

    def subscription_ready(self, err):
        if err: print(err)
        self.collections_ready += 1

        if self.collections_ready == 2:
            self.state = 'connected'
    
    def added(self, collection, _id, fields):
        if collection == 'mediaplaylists':
            self.playlistselect.added(_id, fields)
        elif collection == 'media':
            self.playlistcontent.added(_id, fields)

    def changed(self, collection, _id, fields, cleared):
        if collection == 'mediaplaylists':
            self.playlistselect.changed(_id, fields)
            
            if _id == self.current_playlist:
                self.playlistcontent.update_from_playlist()
                
        elif collection == 'media':
            self.playlistcontent.changed(_id, fields)

    def removed(self, collection, _id):
        if collection == 'mediaplaylists':
            self.playlistselect.removed(_id)

            if _id == self.current_playlist:
                self.playlistcontent.update_from_playlist()

        elif collection == 'media':
            self.playlistcontent.removed(_id)
            
    def change_playlist(self, _id):
        if not _id == self.current_playlist:
            self.current_playlist = _id
            self.playlistcontent.update_from_playlist()

    def get_application_config(self):
        return super(MediaPlayer, self).get_application_config('~/.%(appname)s.ini')

    def build_config(self, config):
        config.setdefaults('connection', {
            'server': 'localhost:3000',
            'autoconnect': False
        })
   
    def toggle_fullscreen(self, thing, touch):        
        if not self.ui.layout.collide_point(*touch.pos):
            if self.fullscreen: Window.fullscreen = 0
            else: Window.fullscreen = 'auto'
            self.fullscreen = not self.fullscreen
    
    def on_motion(self, *args):
        if self.player: self.player.on_motion(*args)
    
    def play_media(self, index):
        self.player = VideoPlayer(
            mediaplayer = self, playlist = self.playlistcontent.data, index = int(index),
            state = 'play', options = {'allow_stretch': True}
        )

        self.master.remove_widget(self.menucontainer)
        self.master.add_widget(self.player)
    
    def close_media(self):
        self.player.stop()
        self.master.remove_widget(self.player)
        self.master.add_widget(self.menucontainer)

        self.player = None
    
    def shuffle_pressed(self, button, value):
        self.shuffle = True if value is 'down' else False
        self.playlistcontent.data_sort()
    
    def fullscreen_pressed(self, button, value):
        if value is 'down': Window.fullscreen = 'auto'
        else: Window.fullscreen = 0

    def build_main_ui(self):
        self.master.clear_widgets()
        del self.connectionui
        
        self.menucontainer = BoxLayout(orientation = 'vertical')
        self.master.add_widget(self.menucontainer)
        
        self.menubar = MenuBar(size_hint = (1, 0.1))
        self.menucontainer.add_widget(self.menubar)
        
        self.menubar.content.shuffle.bind(state = self.shuffle_pressed)
        self.menubar.content.fullscreen.bind(state = self.fullscreen_pressed)
        
        self.panecontainer = BoxLayout()
        self.menucontainer.add_widget(self.panecontainer)
        
        self.playlistselect = PlaylistSelectPane(self, size_hint = (0.3, 1))
        self.panecontainer.add_widget(self.playlistselect)
                
        self.playlistcontent = PlaylistContentPane(self, size_hint = (0.7, 1))
        self.panecontainer.add_widget(self.playlistcontent)
        
    def build(self):
        self.title = 'Cedar Media Player'

        # TODO make icon!        
        #if kivy.utils.platform is 'windows':
        #    self.icon = 'logo/logo-128x128.png'
        #else:
        #    self.icon = 'logo/logo-1024x1024.png'
        
        Window.bind(on_motion = self.on_motion, mouse_pos = self.on_motion)

        self.master = FloatLayout()
        self.player = None

        self.connectionui = ConnectionUI(self, pos_hint = {'center_x': .5, 'center_y': .5}, size_hint = (0.6, 0.2))
        self.master.add_widget(self.connectionui)
        
        return self.master    
