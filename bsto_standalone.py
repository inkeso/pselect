#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import plugins.bsto

# favorites are stored in the current directory in a file called
# bsto.favorites (see bspconfig.py)
# but you can set a different file:
#plugins.bsto.bstoinfo.Bsto.FavFile = "/home/iks/narf"

plugins.bsto.standalone(
    # initial window-size. Tuple of (X,Y) or "fullscreen"
    size = (1024,768),
    #"Size" : "fullscreen",

    # which mediaplayer do you use? I really like mplayer
    playerCmd = "mplayer -fs '%s'")

