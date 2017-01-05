#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This is a plugin for adding burning-series (bs.to) to the filetree
"""

import gtk
import bstoinfo

bsto = None

#def bstokeypressed(win, evt, app):
#    global bsto
#    # bsto-specific eventhandler
#    bsto.on_keypressed(win, evt)
#    # call original handler as well
#    app.list_keypressed(win, evt)

def launchonce(app):
    global bsto

    # load favorites into tree
    selected = app.treeview.get_cursor()[0]
    citer = app.treestore.get_iter(selected)
    if not app.treestore.iter_has_child(citer):
        bsto.populatefavorites(node=citer)
        app.treeview.expand_row(selected, False)
        while gtk.events_pending(): gtk.main_iteration()
        if not bsto.populatebsto(node=citer):
            bsto.treestore.remove(bsto.faviter)

def infiltrate(app):
    """
    This function is called, after the main filetree is build. It has full access
    to gktgui.MainWindow instance, so be careful.
    """
    global piter, faviter, bsto, populatedcallback
    bstoinfo.Bsto.FavFile = bstoinfo.os.path.join(app.prefix, bstoinfo.bspconfig.favorites)
    bsto = bstoinfo.Bsto()
    
    piter = app.treestore.append(None, [
         "Serien Online", # Name
         "",        # Length/Duration. Should be in the format "H:MM:SS" or "MM:SS"
         "bs.to",   # Resolution. May be an arbitrary string.
         "",        # Number of audiochannels
         "",        # Size. May also be something else.
         "Now",     # Modification Time. Or any other string. In this case: Genere, Series, Season
         "",        # path/URI/URL to something, mplayer can play
         launchonce, # an event-handler "row-activate". Gets the app as parameter.
         bsto.on_cursor # an event-handler which get triggerd, when a row gets selected
    ])

    # overwrite the default keypress-handler. This is evil, because other plugins 
    # may do this as well and things can interfere quite severely.
    #app.treeview.connect("key_press_event", bstokeypressed, app)
    
    # set treestore and -view as well as infoframe and playback-function to
    # the corresponding parts of the host (PSelect)
    bsto.treestore = app.treestore
    bsto.treeview = app.treeview
    bsto.infoframe = app.rightframe
    bsto.playback = app.mplayer

def standalone(size, playerCmd):
    app = bstoinfo.Bsto()
    if app.mainwindow(size, playerCmd): gtk.main()
