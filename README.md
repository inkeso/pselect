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
        - some others by using [youtube-dl] \(check `plugins/libs/streamhoster.py`\)
        - for series: remember last watched episode
        - bookmark your favorite series
- Only tested on linux, should be portable to OSX. Windows may be a bit difficult.

## Screenshots
TODO. (please send your screenshots!)

## Installation / Configuration
- You need python 2.7 (i think 2.6 will also work, but didn't test it)
- pygtk and pywebkitgtk (find the corresponding packages of your distribution)
- Probably also python2-scandir for faster startup (scaning file tree)
- You _should_ have a font with emojis (like ttf-symbola or ttf-ancient-fonts) otherwise *c3tv* my look a bit weird.
- Download / clone this repo somewhere.
- If you want to use [youtube-dl] (to decode some more streamhosters within *kinox* or *bsto'), download the binary and place it in this directory or install it via your package-manager.
- On slow machines (such as the RasPi) it is beneficial to extract the binary (yes, you read that right, `7z x youtube-dl ; mv __main__.py youtube-dl`).

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
`↓`,`↑` | Move cursor
`Return` | Expand/collapse folder or Play selected Item
`F9`  | Focus main filelist
`F10` | Play all playlists / Execute special action from plugin
`Esc` | Quit

Playlists only work for local files, not for streams:

key | function
--- | ---
`1` | Add complete video to playlist 1
`2` | Add snippet (up to 3 min) to playlist 1 if cursor is on a file. If it's on a folder, select random files from it, until the playlist is 30 minutes longer. (You may adjust those values in the last function in `gtkgui.py`)
`3` | Focus playlist 1
`4`,`5`,`6` | same for playlist 2
`7`,`8`,`9` | same for playlist 3
`*`,`0`,`#` | same for playlist 4
`Del` | remove currently highlighted video from active playlist

The special action (`F10`) for the three stream-plugins (*c3tv*, *bsto*, *kinox*):
If the cursor is on a stream (and not on a folder) a mirror selection dialog will pop up.

For *bsto* only: if the cursor is on a series-folder, `F10` will add that series to your favorites (or removes it, if it already is present), this will also work from the favorites folder (obviously only for removing).

The plugin will save the last viewed episode for each series and overall.
If you open a series-folder the first time (per session) and have already watched an episode, the cursor will jump to the corresponding position.


## Disclaimer
Again, this was never intended to be userfriendly. You almost always have to read / modify code to make it do want you want.
Apart from this README there is no documentation, you have to look through the source (which is not that much).
This piece of software relies on several 3rd party-libs and programs: 
- python 2
- pygtk
- webkit2
- [odict] _(version 0.2.2 bundled → `plugins/libs/odict.py`)_
- [beautifulsoup]
- [scandir] _(optional for faster file-scan)_
- [youtube-dl] _(optional)_
- [mplayer] OR [mpv] OR [omxplayer]
- [mediainfo] _(optional)_

[beautifulsoup]: https://www.crummy.com/software/BeautifulSoup/
[scandir]: https://github.com/benhoyt/scandir
[exiftool]: http://www.sno.phy.queensu.ca/~phil/exiftool/
[mediainfo]: https://mediaarea.net/en/MediaInfo
[mplayer]: http://www.mplayerhq.hu
[mpv]: https://github.com/mpv-player/mpv
[odict]: http://www.voidspace.org.uk/python/odict.html
[omxplayer]: http://elinux.org/Omxplayer
[youtube-dl]: https://rg3.github.io/youtube-dl/
