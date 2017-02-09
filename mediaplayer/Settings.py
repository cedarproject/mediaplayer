class settings:
    font = 'Lato-Regular'
    font_selected = 'Lato-Bold'
    font_size = 16
    
    icon_font = '/usr/share/fonts/fontawesome/FontAwesome.otf'
    icon_size = 32

    icon_wrap = lambda i, s = icon_size, f = icon_font: '[font={}][size={}]{}[/size][/font]'.format(f, s, i)
    
    icon_play = icon_wrap('')
    icon_pause = icon_wrap('')
    icon_close = icon_wrap('', icon_size * 2)
    icon_shuffle = icon_wrap('')
    icon_fullscreen = icon_wrap('')
