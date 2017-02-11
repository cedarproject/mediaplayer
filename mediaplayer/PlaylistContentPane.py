try:
    import urllib.parse
    def escape_url(url): return urllib.parse.quote(url)
except ImportError:
    import urllib
    def escape_url(url): return urllib.quote(url)

import random

from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ListProperty, ObjectProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.boxlayout import BoxLayout

from .Settings import settings

Builder.load_string('''
<PlaylistContentItem>:
    id: item
    size_hint: 1, 0.1
    padding: (16, 8)
    spacing: 5

    PlaylistContentImage:
        size_hint: None, 1
        pos_hint: {{'left': 0}}
        allow_stretch: True
        source: item.thumburi

    BoxLayout:
        id: labels
        size_hint: .9, 1
        pos_hint: {{'right': 0}}
        padding: (8, 4)
        orientation: 'vertical'

        Label:
            text: item.title
            color: (1, 1, 1, 1)
            font_name: '{0.font}'
            font_size: {0.font_size} * 1.5
            text_size: labels.width, None
            size: self.texture_size
            halign: 'left'
    
        Label:
            text: item.type + item.duration_formatted + '    ' + ', '.join(('"' + tag + '"' for tag in item.tags))
            font_name: '{0.font}'
            font_size: {0.font_size}
            text_size: labels.width, None
            size: self.texture_size
            halign: 'left'

<PlaylistContentPane>:
    viewclass: 'PlaylistContentItem'
    
    PlaylistContentLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
'''.format(settings))

class PlaylistContentImage(AsyncImage):
    # Workaround for an AsyncImage bug
    def _on_source_load(self, *args, **kwargs):
        if self._coreimage:
            super(PlaylistContentImage, self)._on_source_load(*args, **kwargs)

class PlaylistContentLayout(RecycleBoxLayout): pass

class PlaylistContentItem(ButtonBehavior, RecycleDataViewBehavior, BoxLayout):
    title = StringProperty()
    thumburi = StringProperty()
    type = StringProperty()
    duration = NumericProperty()
    duration_formatted = StringProperty()
    tags = ListProperty()
    uri = StringProperty()
    mediaplayer = ObjectProperty()
    
    index = NumericProperty()

    def on_release(self):
        self.mediaplayer.play_media(self.index)


class PlaylistContentPane(RecycleView):
    def __init__(self, mediaplayer, **kwargs):
        super(PlaylistContentPane, self).__init__(**kwargs)
        
        self.mediaplayer = mediaplayer
        self.meteor = self.mediaplayer.meteor
        
        self.data = []

    def get_index_from_id(self, _id):
        for index, item in enumerate(self.data):
            if item['_id'] == _id: return index
        return -1
            
    def data_sort(self):
        if self.mediaplayer.shuffle:
            random.shuffle(self.data)
        else:
            if self.mediaplayer.current_playlist == 'special_all_media':
                self.data = sorted(self.data, key = lambda m: m['title'].lower())
            
            else:
                playlist = self.meteor.find_one('mediaplaylists', selector = {'_id': self.mediaplayer.current_playlist})
                contents = playlist.get('contents')
                self.data = sorted(self.data, key = lambda m: contents.index(m['_id']))
        
        for i, d in enumerate(self.data): d['index'] = i
    
    def add_data_item(self, new_data):
        new_data['uri'] = 'http://{}/media/static/{}'.format(self.mediaplayer.server, escape_url(new_data.get('location')))
    
        if new_data.get('thumbnail'):
            new_data['thumburi'] = 'http://{}/media/static/{}'.format(self.mediaplayer.server, escape_url(new_data.get('thumbnail')))
        else: new_data['thumburi'] = ''

        if new_data.get('type') in ('audio', 'video'):
            dur = new_data['duration']
            m, s = divmod(dur, 60)
            h, m = divmod(m, 60)
            
            new_data['duration_formatted'] = ' - %d:%02d:%02d' % (h, m, s)
        else:
            new_data['duration'] = 0
            new_data['duration_formatted'] = ''
        
        new_data['mediaplayer'] = self.mediaplayer
        
        self.data.append(new_data)        
    
    def update_from_playlist(self):
        self.data = []

        if self.mediaplayer.current_playlist == 'special_all_media':
            for item in self.meteor.find('media'): self.add_data_item(dict(item))
        
        else:
            playlist = self.meteor.find_one('mediaplaylists', selector = {'_id': self.mediaplayer.current_playlist})
            contents = playlist.get('contents')

            for _id in contents:
                item = self.meteor.find_one('media', selector = {'_id': _id})
                self.add_data_item(dict(item))
        
        self.data_sort()
        self.refresh_from_data()
    
    def added(self, _id, fields):
        if _id == self.mediaplayer.current_playlist or self.mediaplayer.current_playlist == 'special_all_media':
            new_data = fields
            new_data['_id'] = _id

            self.add_data_item(new_data)
            self.data_sort()
            self.refresh_from_data()
            
    def changed(self, _id, fields):
        index = self.get_index_from_id(_id)
        if not index == -1:
            self.data[index].update(fields)
            
            self.data_sort()
            self.refresh_from_data()        

    def removed(self, _id):
        index = self.get_index_from_id(_id)
        if not index == -1:
            self.data.remove(self.data[index])
            
            self.refresh_from_data()        
