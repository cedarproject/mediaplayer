from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from .NavigableBehavior import NavigableBehavior
from .Settings import settings

Builder.load_string('''
<PlaylistSelectItem>:
    font_name: '{0.font_selected}' if self.selected else '{0.font}'
    font_size: {0.font_size} * 1.25
    text_size: root.width, None
    halign: 'left'
    color: (.6, 1, .7, 1) if self.selected else (1, 1, 1, 1)
    bold: self.selected
    text: self.title
    shorten: True

<PlaylistSelectPane>:
    viewclass: 'PlaylistSelectItem'
    PlaylistSelectLayout:
        spacing: 5
        padding: (8, 4)
        default_size: None, dp(20)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        multiselect: False
        touch_multiselect: False
'''.format(settings))


class PlaylistSelectLayout(LayoutSelectionBehavior, RecycleBoxLayout): pass

class PlaylistSelectItem(NavigableBehavior, RecycleDataViewBehavior, Label):
    title = StringProperty()
    mediaplayer = ObjectProperty()

    index = NumericProperty()
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    
    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        val = super(PlaylistSelectItem, self).refresh_view_attrs(rv, index, data)
        self.mediaplayer.map_playlistselect[self.index] = self
        return val
        
    def on_touch_down(self, touch):
        if super(PlaylistSelectItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected
        if is_selected:
            self.mediaplayer.change_playlist(rv.data[index]['_id'])

class PlaylistSelectPane(RecycleView):
    def __init__(self, mediaplayer, **kwargs):
        super(PlaylistSelectPane, self).__init__(**kwargs)
        
        self.mediaplayer = mediaplayer
        
        self.all_media = {'_id': 'special_all_media', 'title': 'All Media', 'mediaplayer': self.mediaplayer, 'index': 0}
        
        self.data = [self.all_media]
        
    def get_index_from_id(self, _id):
        for index, playlist in enumerate(self.data):
            if playlist['_id'] == _id: return index
        return -1
    
    def data_sort(self):
        self.data.remove(self.all_media)
        self.data = sorted(self.data, key = lambda m: m['title'])
        self.data.insert(0, self.all_media)
        
        for index, item in enumerate(self.data): item['index'] = index
    
    def added(self, _id, fields):
        self.data.append({
            '_id': _id,
            'title': fields['title'],
            'mediaplayer': self.mediaplayer
        })
        
        self.data_sort()
        self.refresh_from_data()
    
    def changed(self, _id, fields):
        if fields.get('title'):
            index = self.get_index_from_id(_id)
            if not index == -1:
                self.data[index]['title'] = fields['title']
            
            self.data_sort()
            self.refresh_from_data()
    
    def removed(self, _id):
        index = self.get_index_from_id(_id)
        if not index == -1:
            self.data.remove(self.data[index])
            
            self.refresh_from_data()
