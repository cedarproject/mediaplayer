# Cedar Media Player
Plays media files stored on a Cedar server. Currently in development, not yet functional.


# Working Notes

### Flow
On startup, prompt for a server to connect to. List any previous servers by title and address, with the most recent on as default.

After connection show a two-pane interface, with All Media and a list of playlists on the left and the selected item's contents on the right.

### UI
Left pane:
    All media meta-playlist
    List of playlists
    
    At the bottom: Disconnect from server

Right pane:
    A menubar with the following entries:
        Search box - filters the current playlist by search parameters, searching titles and tags
        Shuffle - Randomize the order of media shown
        Play All - Start playing all the media in the current view
        Fullscreen - Duh

    A list of media filtered by left pane's selection and current search parameters
    When media items are played:
        A list of the item(s) to be played is created
        The Playback UI is opened

Playback UI:
	Base on Kivy VideoPlayer, but modify so controls hide after several seconds with no mouse/touch input.

### Misc

Make compatible with TV remotes over CEC for use on the Raspberry Pi.
