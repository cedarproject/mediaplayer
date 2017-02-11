# -*- coding: utf-8 -*-

from kivy.uix.actionbar import ActionBar, ActionView, ActionPrevious, ActionOverflow, ActionButton, ActionToggleButton

from .Settings import settings

class MenuBar(ActionBar):
    def __init__(self, *args, **kwargs):
        super(MenuBar, self).__init__(*args, **kwargs)
        
        self.content = MenuBarContent()
        self.add_widget(self.content)


class MenuBarContent(ActionView):
    def __init__(self, *args, **kwargs):
        super(MenuBarContent, self).__init__(*args, **kwargs)

        button_settings = {
            'font_name': settings.font,
            'font_size': settings.font_size,
            'markup': True
        }
        
        # TODO icon!
        self.add_widget(ActionPrevious(with_previous = False))
        self.add_widget(ActionOverflow())
        
        self.shuffle = ActionToggleButton(text = settings.icon_shuffle + ' Shuffle', **button_settings)
        self.fullscreen = ActionToggleButton(text = settings.icon_fullscreen + ' Fullscreen', **button_settings)
        
        self.add_widget(self.shuffle)
        self.add_widget(self.fullscreen)
