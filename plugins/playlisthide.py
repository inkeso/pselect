#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This plugin hides the playlist, if it's empty (by moving the grip of the HPaned)
"""

# Globals
oldupdate = None
app = None

# Config. Set both to -1 to deactivate plugin, otherwise pixel-values would be nice.
OffsetOn  = -1
OffsetOff = -1

def checkplaylists():
    global app
    
    apll = 0
    for pli in app.playlists:
        apll += len(pli.playlist.playlist)
    
    app.rightframe.get_child()
    if apll == 0 and app.rightframe.get_child() == app.pltab:
        app.mainhpan.set_position(OffsetOff)
        
    else:
        app.mainhpan.set_position(OffsetOn)

def newselectedhover(treeview, void=None):
    global app
    app.selectedhover(treeview)
    checkplaylists()

def newupdate():
    global oldupdate
    oldupdate()
    checkplaylists()


def infiltrate(ap):
    """
    This function is called, after the main filetree is build. It has full access
    to gktgui.MainWindow instance, so be careful.
    """
    if OffsetOn == -1 and OffsetOn == -1: 
        print "\nPlaylistHide-plugin: OffsetOn / OffsetOff not set. Plugin is inactive"
        return
    
    global oldupdate, app
    app = ap
    ap.treeview.connect("cursor-changed", newselectedhover)
    
    # overwrite playlist-update-function (append check)
    oldupdate = app.playlists[0].update
    for i in range(4):
        app.playlists[i].update = newupdate
    
