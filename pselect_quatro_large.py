#!/usr/bin/env python2
# -*- coding: utf-8 -*-

########################################################################
# SteroiX-Config. Four Playlists, big fonts, no frills
########################################################################

# set custom gtk-theme
import os, sys
#os.environ["GTK2_RC_FILES"]=os.path.join(sys.path[0],"gtkrc/large-gtkrc-2.0")
os.environ["GTK2_RC_FILES"]=os.path.join(sys.path[0],"gtkrc/gtk_dark_large_ambiance")

import gtkgui

plugins = ("pregui", "c3tv")

def oninit(app): # customize gui befor it is drawn
    app.win.set_decorated(False)
    app.treeview.set_headers_visible(False)
    # swap panels and insert padding on the left side (second monitor is smaller)
    app.mainhpan.remove(app.rightframe)
    app.mainhpan.remove(app.leftframe)
    app.vpan = gtkgui.gtk.VPaned()
    dummy = gtkgui.gtk.Image()
    app.mainhpan.remove(app.rightframe)
    app.vpan.pack1(app.rightframe)
    app.vpan.pack2(dummy)
    app.mainhpan.pack1(app.vpan)
    app.mainhpan.pack2(app.leftframe)
    # remove playlist-headers
    for i in range(4): app.playlists[i].treeview.set_headers_visible(False)
    # remove lower controll-area completely
    app.lvbox.remove(app.lowerhbox)
    # set Defaults
    app.postcleanup.set_active(False)

def afterinit():
    # set positions (after main window is realized)
    app.win.resize(3040, 1200)
    app.win.move(0,0)
    app.mainhpan.set_position(1273)
    app.pltab.set_position(500)
    app.pltab_t.set_position(600)
    app.pltab_b.set_position(600)
    app.vpan.set_position(1002)

gtkgui.plugins.pregui.infiltrate = oninit
app = gtkgui.MainWindow("/home/iks/VJ", autostart=afterinit, plugs=plugins, clearcache=False)

# set mplayer-parameters for playlists and row-activate / preview
uni = "--no-border --ontop"
app.parameters = "-geometry 1918x1198+2048+0 -fs "+uni
app.player = "mpv"
for i in range(4): app.playlists[i].parameters = app.parameters

app.playlists[0].playlist.parameters = "-geometry 1918x1198+2048+0 -fs -volume 25 "+uni
app.playlists[1].playlist.parameters = "-geometry 1278x1022+768+0 -fs -volume 25 "+uni
app.playlists[2].playlist.parameters = "-geometry 766x681+0+0 -volume 25 "+uni
app.playlists[3].playlist.parameters = "-geometry 766x681+0+684 -volume 25 "+uni

# here we go
gtkgui.gtk.main()
