from kivy.properties import BooleanProperty
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation

from .Settings import settings

Builder.load_string('''
<NavigableBehavior>:
    canvas.before:
        Color:
            rgba: {settings.color_selected} if self.navigated else (0, 0, 0, 0)
        Line:
            rectangle: (*(c - {settings.line_width_selected} / 2.0 for c in self.pos), *(c + {settings.line_width_selected} / 2.0 for c in self.size))
            width: {settings.line_width_selected}
'''.format(settings = settings))

class NavigableBehavior:
    navigated = BooleanProperty(False)
    
    def on_touch_down(self, *args):
        self.navigated = False
    
    def navigable_activate(self):
        pass


class NavigableManager:
    def __init__(self, mediaplayer):
        self.mediaplayer = mediaplayer
        
        self.current_parent = self.mediaplayer.playlistselect
        self.current_item = 0
        
        self.scroll_anim = None
        
        Window.bind(on_key_down = self.on_key_down)
        
    def get_len_children(self):
        if self.current_parent is self.mediaplayer.playlistselect or self.current_parent is self.mediaplayer.playlistcontent:
            return len(self.current_parent.data)
   
    def get_current_widget(self):
        if self.current_parent is self.mediaplayer.playlistselect:
            return self.mediaplayer.map_playlistselect.get(self.current_item)

        elif self.current_parent is self.mediaplayer.playlistcontent:
            return self.mediaplayer.map_playlistcontent.get(self.current_item)
    
    def on_key_down(self, window, key, scancode = None, codepoint = None, modifier = None):
        previous_item = int(self.current_item)
        previous = self.get_current_widget()

        if previous and previous.navigated:
            previous.navigated = False
            
            if key == 273: self.up()
            if key == 274: self.down()
            if key == 275: self.right()
            if key == 276: self.left()
    
        self.activate_current()

    def activate_current(self, *args):
        current = self.get_current_widget()
        
        if current:
            current.navigated = True
            if self.current_parent is self.mediaplayer.playlistselect or self.current_parent is self.mediaplayer.playlistcontent:
                # This is an ugly solution to scrolling a RecycleView to a given widget. Since all the widgets (should) have the same height,
                # multiply that height by the index of the desired widget, then animate scrolling to that X-value.
                
                if self.scroll_anim: self.scroll_anim.cancel_all(self.current_parent)
                
                target_value = 1.0 - self.current_parent.convert_distance_to_scroll(
                    0,
                    (self.current_parent.children[0].children[0].height * self.current_item) - (self.current_parent.height / 2.0)
                )[1]
                
                self.scroll_anim = Animation(scroll_y = target_value, d = 0.1, t = 'linear')
                self.scroll_anim.start(self.current_parent)

        else:
            Clock.schedule_once(self.activate_current, 0.05)
                
    def left(self):
        previous_parent = self.current_parent
    
        if self.current_parent == self.mediaplayer.playlistcontent:
            self.current_parent = self.mediaplayer.playlistselect
            
        if not self.current_parent is previous_parent:
            self.current_item = 0
            
        # TODO menubar logic
            
    def right(self):
        previous_parent = self.current_parent
        
        if self.current_parent == self.mediaplayer.playlistselect:
            self.current_parent = self.mediaplayer.playlistcontent
        
        if not self.current_parent is previous_parent:
            self.current_item = 0

        # TODO menubar logic
    
    def up(self):
        # TODO menubar logic

        if not self.current_item == 0:        
            self.current_item -= 1
    
    def down(self):
        # TODO menubar logic
        
        if not self.current_item + 1 == self.get_len_children():    
            self.current_item += 1
