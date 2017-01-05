#!/usr/bin/env python2
# -*- coding: utf-8 -*-

########################################################################
# A simple Mediacenter-like config
########################################################################

import os, sys, gtkgui

plugins = ('clocky', 'bsto', 'kinox', 'c3tv', 'shexec')

app = gtkgui.MainWindow("videos", plugs=plugins, clearcache=False)
app.win.maximize()
app.mainhpan.set_position(1000)

# only keep first playlist
app.pltab_t.remove(app.playlists[1].widget)
app.pltab.remove(app.pltab_b)

app.parameters = "-fs"
app.player = "mplayer"

# Start!
gtkgui.gtk.main()
