#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This is a plugin for kinox.to
"""

import gtk
import kinoxinfo

kinox = None

#def kinoxkeypressed(win, evt, app):
#    global kinox
#    # kinox-specific eventhandler
#    kinox.on_keypressed(win, evt)
#    # call original handler as well
#    app.list_keypressed(win, evt)


def infiltrate(app):
    """
    This function is called, after the main filetree is build. It has full access
    to gktgui.MainWindow instance, so be careful.
    """
    global kinox
    kinox = kinoxinfo.KinoxGUI()
    # set treestore and -view as well as infoframe and playback-function to
    # the corresponding parts of the host (PSelect)
    kinox.treestore = app.treestore
    kinox.movielist = app.treeview
    kinox.infoframe = app.rightframe
    kinox.playback = app.mplayer
    # create main tree
    kinox.appendTree(node=app.treestore.append(None, 
        ("kinox.to",) + ("",)*6 + (kinox.on_activate, kinox.on_cursor)
    ))

    # overwrite the default keypress-handler. This is evil, because other plugins 
    # may do this as well and things can interfere quite severely.
    # disabled for now, because of conflicting key
    #app.treeview.connect("key_press_event", kinoxkeypressed, app)
    
def standalone(size, playerCmd):
    """
    Start stand-alone instance
    """
    global kinox
    kinox = kinoxinfo.KinoxGUI()
    kinox.mainwindow(size, playerCmd)
