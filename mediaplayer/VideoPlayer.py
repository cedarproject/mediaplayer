# This is a modified version of Kivy's VideoPlayer UI element. Refer to the file KIVY_LICENSE for copyright and licensing details.

from json import load
from os.path import exists
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, DictProperty, OptionProperty
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.core.audio import SoundLoader
from kivy.uix.image import AsyncImage
from kivy.uix.video import Image
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.config import Config
from kivy.core.window import Window

from .Settings import settings

Builder.load_string('''
<CMPVideoPlayer>:
    container: container
    controls: controls
    anchor_y: 'bottom'
    
    canvas:
        Color:
            rgba: (0, 0, 0, 1)
        Rectangle:
            size: self.size
            pos: self.pos

    FloatLayout:
        id: container
        size_hint: (1, 1)
        
    FloatLayout:
        id: controls    
        size_hint: (1, 1)

        AnchorLayout:
            size_hint: (1, 1)
            anchor_x: 'center'
            anchor_y: 'bottom'

            GridLayout:
                rows: 1
                size_hint: (0.8, None)
                height: 64
                
                canvas:
                    Color:
                        rgba: (0, 0, 0, 0.25)
                    Rectangle:
                        size: self.size
                        pos: self.pos
                
                CMPVideoPlayerPrev:
                    size_hint_x: None
                    video: root
                    markup: True
                    width: {settings.icon_size} * 1.5
                    text: "{settings.icon_prev}"

                CMPVideoPlayerPlayPause:
                    size_hint_x: None
                    video: root
                    markup: True
                    width: {settings.icon_size} * 1.5
                    text: "{settings.icon_pause}" if root.state == 'play' else "{settings.icon_play}"

                CMPVideoPlayerNext:
                    size_hint_x: None
                    video: root
                    markup: True
                    width: {settings.icon_size} * 1.5
                    text: "{settings.icon_next}"

                Widget:
                    size_hint_x: None
                    width: 5

                CMPVideoPlayerProgressBar:
                    video: root
                    max: max(root.duration, root.position, 1)
                    value: root.position

                CMPVideoPlayerClose:
                    size_hint_x: None
                    video: root
                    markup: True
                    width: {settings.icon_size} * 2
                    text: "{settings.icon_close}"
                    
<CMPAudioInfo>:
    id: info
    spacing: 16

    AsyncImage:
        source: info.thumburi
        allow_stretch: True

    Label:
        text: info.title
        color: (1, 1, 1, 1)
        font_name: '{settings.font}'
        font_size: {settings.font_size} * 2
        halign: 'center'
        valign: 'center'
'''.format(settings = settings))

class CMPAudioInfo(BoxLayout):
    thumburi = StringProperty()
    title = StringProperty()

class CMPVideoPlayerPrev(Label):
    video = ObjectProperty(None)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos): self.video.prev()

class CMPVideoPlayerPlayPause(Label):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.video.state == 'play':
                self.video.state = 'pause'
            else:
                self.video.state = 'play'
            return True

class CMPVideoPlayerNext(Label):
    video = ObjectProperty(None)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos): self.video.next()

class CMPVideoPlayerClose(Label):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.video.state = 'stop'
            self.video.mediaplayer.close_media()
            return True


class CMPVideoPlayerProgressBar(ProgressBar):
    video = ObjectProperty(None)
    seek = NumericProperty(None, allownone=True)
    alpha = NumericProperty(1.)

    def __init__(self, **kwargs):
        super(CMPVideoPlayerProgressBar, self).__init__(**kwargs)
        self.bubble = Factory.Bubble(size=(50, 44))
        self.bubble_label = Factory.Label(text='0:00')
        self.bubble.add_widget(self.bubble_label)
        self.add_widget(self.bubble)

        update = self._update_bubble
        fbind = self.fbind
        fbind('pos', update)
        fbind('size', update)
        fbind('seek', update)

    def on_video(self, instance, value):
        self.video.bind(position=self._update_bubble,
                        state=self._showhide_bubble)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self._show_bubble()
        touch.grab(self)
        self._update_seek(touch.x)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        self._update_seek(touch.x)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        if self.seek:
            self.video.seek(self.seek)
        self.seek = None
        self._hide_bubble()
        return True

    def _update_seek(self, x):
        if self.width == 0:
            return
        x = max(self.x, min(self.right, x)) - self.x
        self.seek = x / float(self.width)

    def _show_bubble(self):
        self.alpha = 1
        Animation.stop_all(self, 'alpha')

    def _hide_bubble(self):
        self.alpha = 1.
        Animation(alpha=0, d=4, t='in_out_expo').start(self)

    def on_alpha(self, instance, value):
        self.bubble.background_color = (1, 1, 1, value)
        self.bubble_label.color = (1, 1, 1, value)

    def _update_bubble(self, *l):
        seek = self.seek
        if self.seek is None:
            if self.video.duration == 0:
                seek = 0
            else:
                seek = self.video.position / self.video.duration
        # convert to minutes:seconds
        d = self.video.duration * seek
        minutes = int(d / 60)
        seconds = int(d - (minutes * 60))
        # fix bubble label & position
        self.bubble_label.text = '%d:%02d' % (minutes, seconds)
        self.bubble.center_x = self.x + seek * self.width
        self.bubble.y = self.center[1]

    def _showhide_bubble(self, instance, value):
        if value == 'play':
            self._hide_bubble()
        else:
            self._show_bubble()

class CMPVideoPlayer(AnchorLayout):
    source = StringProperty('')

    duration = NumericProperty(-1)

    position = NumericProperty(0)

    volume = NumericProperty(1.0)

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))

    play = BooleanProperty(False)

    options = DictProperty({})
    
    control_timeout = NumericProperty(2)
    
    mediaplayer = ObjectProperty()

    # internals
    container = ObjectProperty(None)
    controls = ObjectProperty(None)

    _video_load_ev = None

    def __init__(self, **kwargs):
        self.mediaplayer = kwargs['mediaplayer']
        self.playlist = kwargs['playlist']
        self.index = kwargs['index']
        
        del kwargs['mediaplayer'], kwargs['playlist'], kwargs['index']
    
        self._video = None
        self._audio = None
        self._image = None

        self._audio_position_update_handle = None

        super(CMPVideoPlayer, self).__init__(**kwargs)
        
        self._control_shown = True
        self._control_animation = None
        self._control_timeout_clock = Clock.schedule_once(self._on_control_timeout, self.control_timeout)
        
        self.load_media(self.playlist[self.index])
    
    def _on_control_timeout(self, dt):
        if self._control_shown:
            self._control_shown = False

            if self._control_animation: self._control_animation.cancel(self.controls)
            self._control_animation = Animation(opacity = 0, d = 0.25, t = 'linear')
            self._control_animation.on_complete = self._control_anim_complete
            self._control_animation.start(self.controls)

            Window.show_cursor = False
        
    def on_motion(self, *args):
        if self._control_shown:
            self._control_timeout_clock.cancel()
            self._control_timeout_clock = Clock.schedule_once(self._on_control_timeout, self.control_timeout)
        
        else:
            self._control_shown = True
            
            if self._control_animation: self._control_animation.cancel(self.controls)
            self._control_animation = Animation(opacity = 1, d = 0.25, t = 'linear')
            self._control_animation.on_complete = self._control_anim_complete
            self._control_animation.start(self.controls)

            Window.show_cursor = True


    def _control_anim_complete(self, a):
        self._control_animation = None
    
    def stop(self):
        self.remove_current()
        self._control_timeout_clock.cancel()        
        Window.show_cursor = True
    
    def prev(self):
        if self.index == 0: self.index = len(self.playlist) - 1
        else: self.index -= 1

        self.load_media(self.playlist[self.index])
    
    def next(self):
        if self.index == len(self.playlist) - 1: self.index = 0
        else: self.index += 1

        self.load_media(self.playlist[self.index])
    
    def eos(self, *args):
        self.next()
    
    def remove_current(self):
        if self._video:
            self._video.unload()
            self._video = None
        if self._audio:
            self._audio.unload()
            self._audio = None

        if self._audio_position_update_handle:
            self._audio_position_update_handle.cancel()
            self._audio_position_update_handle = None

        self.container.clear_widgets()
    
    def load_media(self, media):
        self.remove_current()
        
        if media['type'] == 'video':
            self._video = Video(
                source = media['uri'], state = 'play',
                volume = self.volume, pos_hint = {'x': 0, 'y': 0},
                **self.options
            )
            
            self._video.bind(
                duration = self.setter('duration'),
                position = self.setter('position'),
                state = self._set_state,
                eos = self.eos
             )

            self.container.add_widget(self._video)
          
        if media['type'] == 'audio':
            self.container.add_widget(CMPAudioInfo(thumburi = media['thumburi'], title = media['title']))
        
            self._audio = SoundLoader.load(media['uri'])
            
            self.duration = media['duration']
            
            self._audio.bind(
                state = self._set_state
            )
            
            self.audio_position_update_handle = Clock.schedule_interval(self._audio_position_update, 0.25)
            
            self._audio.load()
            self._audio.play()
        
        if media['type'] == 'image':
            self.container.add_widget(AsyncImage(source = media['uri'], allow_stretch = True))
        
        self.state = 'play'
    
    def _audio_position_update(self, dt):
        if self._audio and self._audio.state == 'play':
            self.position = self._audio.get_pos()

    def on_state(self, instance, value):
        if self._video:
            self._video.state = value

        elif self._audio:
            if value == 'play':
                self._audio.play()
                self._audio.seek(self.position)
                
            elif value == 'pause': self._audio.stop()
            
            elif value == 'stop':
                if self.duration - self.position < 0.5: self.eos()

    def _set_state(self, instance, value):
        self.state = value

    def on_play(self, instance, value):
        value = 'play' if value else 'stop'
        return self.on_state(instance, value)

    def seek(self, percent):
        if self._video:
            self._video.seek(percent)
        
        if self._audio:
            target = self.duration * percent
            self._audio.seek(target)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        
        return super(CMPVideoPlayer, self).on_touch_down(touch)
