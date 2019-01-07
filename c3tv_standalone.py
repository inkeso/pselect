#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import plugins.c3tv

plugins.c3tv.standalone(
    # initial window-size. Tuple of (X,Y) or "fullscreen"
    size = (1024,768),
    #size = "fullscreen",

    # which mediaplayer do you use? I really like mplayer
    playerCmd = "mpv -fs '%s'")

