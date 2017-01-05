#!/usr/bin/env python2
# -*- coding: utf-8 -*-

########################################################################
# Nextlevel-Config. One Playlist, big fonts, low frills
########################################################################

# set custom gtk-theme
import os, sys, subprocess, time
#os.environ["GTK2_RC_FILES"]=os.path.join(sys.path[0],"gtkrc/gtk_clear_dark")
os.environ["GTK2_RC_FILES"]=os.path.join(sys.path[0],"gtkrc/gtk_dark_large_ambiance")

import gtkgui

# (pre)configure plugins
plugins = ('clocky', 'playlisthide', 'pregui', 'mountdev', 'bsto', 'kinox', 'c3tv', 'shexec')
gtkgui.plugins.clocky.DoInstant = True
gtkgui.plugins.playlisthide.OffsetOn  = 1040
gtkgui.plugins.playlisthide.OffsetOff = 1920

# reduce to first playlist and omit quitbutton
def plremove(app):
    app.win.maximize()
    app.pltab_t.remove(app.playlists[1].widget)
    app.pltab.remove(app.pltab_b)
    app.midvbox.remove(app.postframe)
    app.actionvbox.remove(app.quitbutton)
    app.treeview.get_column(0).set_sizing(2)
    app.treeview.get_column(0).set_fixed_width(1300)
    app.treeview.get_column(5).set_visible(False) # hide date
    # set Defaults
    app.postcleanup.set_active(True)

gtkgui.plugins.pregui.infiltrate = plremove

app = gtkgui.MainWindow(os.path.join(sys.path[0],"videos"), autostart=lambda: app.mainhpan.set_position(1920), plugs=plugins)

# set mplayer-parameters for playlists and row-activate / preview
app.parameters = "-fs -softvol -softvol-max 500 -fixed-vo -cache 4096 -msgcolor -msglevel all=2:cplayer=4:decvideo=4:decaudio=4 -msgmodule"
app.playlists[0].parameters = app.parameters
app.playlists[0].playlist.parameters = app.parameters

app.ch6filter = "-channels 6"
app.ch2filter = "-channels 6 -af surround=15,sub=120:5,center=4"

# here we go
gtkgui.gtk.main()

