# This is a modified version of Kivy's VideoPlayer UI element. Refer to the file KIVY_LICENSE for copyright and licensing details.

from json import load
from os.path import exists
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty, DictProperty, OptionProperty
from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.uix.video import Image
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.config import Config
from kivy.core.window import Window

from .Settings import settings

Builder.load_string('''
<CMPVideoPlayerPreview>:
    pos_hint: {{'x': 0, 'y': 0}}
    image_overlay_play: 'atlas://data/images/defaulttheme/player-play-overlay'
    image_loading: 'data/images/image-loading.gif'
    Image:
        source: root.source
        color: (.5, .5, .5, 1)
        pos_hint: {{'x': 0, 'y': 0}}
    Image:
        source: root.image_overlay_play if not root.click_done else root.image_loading
        pos_hint: {{'x': 0, 'y': 0}}

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
            anchor_x: 'right'
            anchor_y: 'top'
            padding: 16
        
            CMPVideoPlayerClose:
                size_hint: (None, None)
                size: self.texture_size
                video: root
                markup: True
                text: "{settings.icon_close}"

        AnchorLayout:
            size_hint: (1, 1)
            anchor_x: 'center'
            anchor_y: 'bottom'

            GridLayout:
                rows: 1
                size_hint: (0.8, None)
                height: '128dp'

                CMPVideoPlayerPlayPause:
                    size_hint_x: None
                    video: root
                    markup: True
                    text: "{settings.icon_pause}" if root.state == 'play' else "{settings.icon_play}"

                Widget:
                    size_hint_x: None
                    width: 5

                CMPVideoPlayerProgressBar:
                    video: root
                    max: max(root.duration, root.position, 1)
                    value: root.position

'''.format(settings = settings))

class CMPVideoPlayerPlayPause(Label):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        '''.. versionchanged:: 1.4.0'''
        if self.collide_point(*touch.pos):
            if self.video.state == 'play':
                self.video.state = 'pause'
            else:
                self.video.state = 'play'
            return True


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
        self.bubble.y = self.top

    def _showhide_bubble(self, instance, value):
        if value == 'play':
            self._hide_bubble()
        else:
            self._show_bubble()


class CMPVideoPlayerPreview(FloatLayout):
    source = ObjectProperty(None)
    video = ObjectProperty(None)
    click_done = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.click_done:
            self.click_done = True
            self.video.state = 'play'
        return True


class CMPVideoPlayer(AnchorLayout):
    '''CMPVideoPlayer class. See module documentation for more information.
    '''

    source = StringProperty('')
    '''Source of the video to read.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to ''.

    .. versionchanged:: 1.4.0
    '''

    thumbnail = StringProperty('')
    '''Thumbnail of the video to show. If None, CMPVideoPlayer will try to find
    the thumbnail from the :attr:`source` + '.png'.

    :attr:`thumbnail` a :class:`~kivy.properties.StringProperty` and defaults
    to ''.

    .. versionchanged:: 1.4.0
    '''

    duration = NumericProperty(-1)
    '''Duration of the video. The duration defaults to -1 and is set to the
    real duration when the video is loaded.

    :attr:`duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1.
    '''

    position = NumericProperty(0)
    '''Position of the video between 0 and :attr:`duration`. The position
    defaults to -1 and is set to the real position when the video is loaded.

    :attr:`position` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1.
    '''

    volume = NumericProperty(1.0)
    '''Volume of the video in the range 0-1. 1 means full volume and 0 means
    mute.

    :attr:`volume` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 1.
    '''

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    '''String, indicates whether to play, pause, or stop the video::

        # start playing the video at creation
        video = CMPVideoPlayer(source='movie.mkv', state='play')

        # create the video, and start later
        video = CMPVideoPlayer(source='movie.mkv')
        # and later
        video.state = 'play'

    :attr:`state` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'stop'.
    '''

    play = BooleanProperty(False)
    '''
    .. deprecated:: 1.4.0
        Use :attr:`state` instead.

    Boolean, indicates whether the video is playing or not. You can start/stop
    the video by setting this property::

        # start playing the video at creation
        video = CMPVideoPlayer(source='movie.mkv', play=True)

        # create the video, and start later
        video = CMPVideoPlayer(source='movie.mkv')
        # and later
        video.play = True

    :attr:`play` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    image_overlay_play = StringProperty(
        'atlas://data/images/defaulttheme/player-play-overlay')
    '''Image filename used to show a "play" overlay when the video has not yet
    started.

    :attr:`image_overlay_play` is a
    :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/player-play-overlay'.

    '''

    image_loading = StringProperty('data/images/image-loading.gif')
    '''Image filename used when the video is loading.

    :attr:`image_loading` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'data/images/image-loading.gif'.
    '''

    image_play = StringProperty(
        'atlas://data/images/defaulttheme/media-playback-start')
    '''Image filename used for the "Play" button.

    :attr:`image_play` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/media-playback-start'.
    '''

    image_stop = StringProperty(
        'atlas://data/images/defaulttheme/media-playback-stop')
    '''Image filename used for the "Stop" button.

    :attr:`image_stop` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/media-playback-stop'.
    '''

    image_pause = StringProperty(
        'atlas://data/images/defaulttheme/media-playback-pause')
    '''Image filename used for the "Pause" button.

    :attr:`image_pause` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/media-playback-pause'.
    '''

    image_volumehigh = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-high')
    '''Image filename used for the volume icon when the volume is high.

    :attr:`image_volumehigh` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/audio-volume-high'.
    '''

    image_volumemedium = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-medium')
    '''Image filename used for the volume icon when the volume is medium.

    :attr:`image_volumemedium` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/audio-volume-medium'.
    '''

    image_volumelow = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-low')
    '''Image filename used for the volume icon when the volume is low.

    :attr:`image_volumelow` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/audio-volume-low'.
    '''

    image_volumemuted = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-muted')
    '''Image filename used for the volume icon when the volume is muted.

    :attr:`image_volumemuted` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/audio-volume-muted'.
    '''

    options = DictProperty({})
    '''Optional parameters can be passed to a :class:`~kivy.uix.video.Video`
    instance with this property.

    :attr:`options` a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''
    
    control_timeout = NumericProperty(3)
    
    mediaplayer = ObjectProperty()

    # internals
    container = ObjectProperty(None)
    controls = ObjectProperty(None)

    _video_load_ev = None

    def __init__(self, **kwargs):
        self._video = None
        self._image = None
        super(CMPVideoPlayer, self).__init__(**kwargs)
        self._load_thumbnail()

        if self.source:
            self._trigger_video_load()
        
        self._control_shown = True
        self._control_animation = None
        self._control_timeout_clock = Clock.schedule_once(self._on_control_timeout, self.control_timeout)
    
    def _on_control_timeout(self, dt):
        if self._control_shown:
            self._control_shown = False

            if self._control_animation: self._control_animation.cancel()
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
            
            if self._control_animation: self._control_animation.cancel()
            self._control_animation = Animation(opacity = 1, d = 0.25, t = 'linear')
            self._control_animation.on_complete = self._control_anim_complete
            self._control_animation.start(self.controls)

            Window.show_cursor = True


    def _control_anim_complete(self, a):
        self._control_animation = None
    
    def stop(self):
        self._control_timeout_clock.cancel()        
        Window.show_cursor = True
            
    def _trigger_video_load(self, *largs):
        ev = self._video_load_ev
        if ev is None:
            ev = self._video_load_ev = Clock.schedule_once(self._do_video_load, -1)

        ev()

    def on_source(self, instance, value):
        # we got a value, try to see if we have an image for it
        self._load_thumbnail()
        if self._video is not None:
            self._video.unload()
            self._video = None
        if value:
            self._trigger_video_load()

    def on_image_overlay_play(self, instance, value):
        self._image.image_overlay_play = value

    def on_image_loading(self, instance, value):
        self._image.image_loading = value

    def _load_thumbnail(self):
        if not self.container:
            return
        self.container.clear_widgets()
        # get the source, remove extension, and use png
        thumbnail = self.thumbnail
        if not thumbnail:
            filename = self.source.rsplit('.', 1)
            thumbnail = filename[0] + '.png'
        self._image = CMPVideoPlayerPreview(source=thumbnail, video=self)
        self.container.add_widget(self._image)

    def on_state(self, instance, value):
        if self._video is not None:
            self._video.state = value

    def _set_state(self, instance, value):
        self.state = value

    def _do_video_load(self, *largs):
        self._video = Video(source=self.source, state=self.state,
                            volume=self.volume, pos_hint={'x': 0, 'y': 0},
                            **self.options)
        self._video.bind(texture=self._play_started,
                         duration=self.setter('duration'),
                         position=self.setter('position'),
                         volume=self.setter('volume'),
                         state=self._set_state)

    def on_play(self, instance, value):
        value = 'play' if value else 'stop'
        return self.on_state(instance, value)

    def on_volume(self, instance, value):
        if not self._video:
            return
        self._video.volume = value

    def seek(self, percent):
        '''Change the position to a percentage of the duration. Percentage must
        be a value between 0-1.

        .. warning::

            Calling seek() before video is loaded has no effect.
        '''
        if not self._video:
            return
        self._video.seek(percent)

    def _play_started(self, instance, value):
        self.container.clear_widgets()
        self.container.add_widget(self._video)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        
        return super(CMPVideoPlayer, self).on_touch_down(touch)
