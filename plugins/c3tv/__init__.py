#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This is a plugin for adding CCC-Videos to the filetree
"""

import gtk
import c3tv

c3 = None

def launchonce(app):
    global c3
    selected = app.treeview.get_cursor()[0]
    citer = app.treestore.get_iter(selected)
    hasChilds = app.treestore.iter_has_child(citer)
    if not hasChilds:
        c3.appendTree(node=citer)
        app.treeview.expand_row(selected, False)

def infiltrate(app):
    """
    This function is called, after the main filetree is build. It has full access
    to gktgui.MainWindow instance, so be careful.
    """
    global c3
    c3 = c3tv.CccTree()
    piter = app.treestore.append(None, [
         "C3TV",    # Name
         "",        # Length/Duration. Should be in the format "H:MM:SS" or "MM:SS"
         "ccc",     # Resolution. May be an arbitrary string.
         "",        # Audiochannels. Set to 2 or 6 to active audiochannel-filters.
         "",        # Size. May also be something else.
         "Now",     # Modification Time. Or any other string.
         "",        # path/URI/URL to something mplayer can play.
         launchonce,# an event-handler "row-activate". Gets the app as parameter.
         c3.on_cursor      # an event-handler which get triggerd, when a row gets selected
    ])
    # set container & overwrite playback-function
    c3.treestore = app.treestore
    c3.movielist = app.treeview
    c3.infoframe = app.rightframe
    c3.playback = app.mplayer

def standalone(size, playerCmd):
    """
    Start stand-alone instance
    """
    global c3
    c3 = c3tv.CccTree()
    c3.mainwindow(size, playerCmd)
