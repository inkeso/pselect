# Pselect
This is a very basic mediacenter-like software based on python 2 and gtk2.
It just shows all the videofiles from a directory in a treeView to select from (for instant viewing or adding to one of the up to 4 playlists).

This piece of software evolved over a very long time (starting from a 90-lines shellscript over 8 years ago), adding features as needed and several rewrites. It still is buggy and not very userfriendly, but it was never intended to be.
It now reads metadata using whatever tool is available (see below) and it has a "plugin"-system, providing support for GUI-modifications or additional sources.

## Features
- Read metadata from videofiles using [mplayer], [omxplayer] or [mediainfo].
- Metadata are cached
- Play videofiles using [mpv], [mplayer] or [omxplayer]
- Up to 4 Playlists (for local files only)
- add random file(s) from a folder and even random chunks from a file.
    - See `gtkgui.py` at the bottom to change lengths and number of randomly added videochunks
    - This feature does not work fully with omxplayer
- Through plugins:
    - Hide empty playlist
    - show a clock (when will the currently selected movie finish?)
    - Mount/unmount other (predefined) devices (see `plugins/mountdev.py`, `videos/additional_devices.pselect`)
    - Execute other programs (see `plugins/shexec.py`, `videos/external_scripts.pselect`)
    - play streams from bs.to, serienstreams.to, kinox.to
        - can decode some streamhosters itself
        - some others by using [youtube-dl] (check `plugins/libs/streamhoster.py`)
        - for series: remember last watched episode
        - bookmark your favorite series
- Only tested on linux, should be portable to OSX. Windows may be a bit difficult.

## Screenshots
TODO. (please send your screenshots!)

## Installation / Configuration
You need python 2.7 (i think 2.6 will also work, but didn't test it), pygtk and pywebkitgtk. You need to find the corresponding packages of your distribution.
download / clone this repo somewhere.
If you want to use [youtube-dl] (to decode some more streamhosters within *kinox* or *bsto'), download the binary and place it in this directory.
Or install it via your package-manager.
On slow machines (such as the RasPi) it is beneficial to extract the binary (yes, you read that right, `7z x youtube-dl ; mv __main__.py youtube-dl`).

There is no way to configure anything within the GUI. Configuration / customization is done via editing the code. So check / copy / edit one of the startup-files:

- `pselect_pi.py` (single playlist, metadata are not shown as columns but in a panel. I use this on a Raspberry Pi as a mediacenter)
- `pselect_quatro_large.py` (all 4 playlists. Be shure to check the mplayer-parameters)
- `pselect_simple_full.py` (one playlist, simplest configuration)
- `pselect_single_clear.py` (one playlist which autohides if empty, some plugins, used for a different mediacenter)

Be sure to at least check the line with gtkgui.MainWindow(...) to point to the correct directory containing your videos.
Note that config for *shexec*, *mountdev* and *bsto* as well as the metadata cache also goes there, so you need write-access.
You can keep the subdirectory "videos" from this repo, edit the example-settings and put some symlinks to your several (potentially write-protected) locations where you're hoarding your movies and stuff.

If you just want to use one of the source-plugins (without processing local files):

- `bsto_standalone.py` (show streams from bs.to and serienstreams.to)
- `c3tv_standalone.py` (show streams from media.ccc.de)
- `kinox_standalone.py` (search kinox)

Look in those files as well before executing them.


## Usage
Meh, you'll figure it out yourself. But here are keyboard-shortcuts (you may change them in `gtkgui.py`):

key | function
--- | ---
`1` | Add complete to PL 1
`2` | Add snippet to PL 1
`3` | Focus PL 1
`4`,`5`,`6` | same for PL 2
`7`,`8`,`9` | for PL 3
`*`,`0`,`#` | for PL 4
`Del` | remove currently highlighted video from active playlist (see below)
`F10` | Play all playlists / Execute special action from plugin
`F9`  | Focus main filelist
`Return` | Play selected Item
`Esc` | Quit

The special action for the three stream-plugins (*c3tv*, *bsto*, *kinox*):
If the cursor is on a stream (and not on a folder) a mirror selection dialog will pop up.

For *bsto* only: if the cursor is on a series-folder, F10 will add that series to your favorites (or removes it, if it already is present)
This will also work from the favorites folder (obviously only for removing)
The plugin will save the last viewed episode for each series and overall.
If you open a series-folder the first time (per session) and have already watched an episode, the cursor will jump to the corresponding position.


## Disclaimer
Again, this was never intended to be userfriendly. You almost always have to read / modify code to make it do want you want.
Apart from this README there is no documentation, you have to look through the source (which is not that much).
This piece of software relies on several 3rd party-libs and programs: 
- python (2.x (I only tested it with 2.7))
- pygtk
- webkit2
- [odict] (bundled → `plugins/libs/odict.py`)
- [beautifulsoup] (bundled →`plugins/libs/bs4`)
- [youtube-dl] (optional, just put the single, executable file `youtube-dl` in the same directory as this program)
- [mplayer] OR [mpv] OR [omxplayer]
- [mediainfo] (optional)


[mplayer]: http://www.mplayerhq.hu
[omxplayer]: http://elinux.org/Omxplayer
[mpv]: https://github.com/mpv-player/mpv
[mediainfo]: https://mediaarea.net/en/MediaInfo
[exiftool]: http://www.sno.phy.queensu.ca/~phil/exiftool/
[youtube-dl]: https://rg3.github.io/youtube-dl/
[odict]: http://www.voidspace.org.uk/python/odict.html
