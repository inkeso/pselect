#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# import gtkgui
# import os
# os.system("mkdir /tmp/empty")
# app = gtkgui.MainWindow("/tmp/empty", plugs=('kinox',))
# gtkgui.gtk.main()
# os.system("rmdir /tmp/empty")


# this should work as well (and is the preferred way to do it):
import plugins.kinox
plugins.kinox.standalone(
    # initial window-size. Tuple of (X,Y) or "fullscreen"
    size = (1024,768),

    # which mediaplayer do you use? I really like mplayer
    playerCmd = "mplayer -fs '%s'")

