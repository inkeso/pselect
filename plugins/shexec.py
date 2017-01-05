#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This is an example plugin for adding "program-launcher" to the filetree
"""

# TODO: Special-action: Kommando vorher bearbeiten



import os, gtk

# initialize custiom widget(s) for this plugin
info = gtk.Label("Execute")
info.set_use_markup(True)
info.set_justify(gtk.JUSTIFY_CENTER)
info.set_alignment(0.5, 0.125)

info.show()


def launch(app):
    """
    Eventhandler for activating an entry, generated below. (Hitting "Enter")
    """
    global info
    print "Exec:", app.getselectedpath()
    while gtk.events_pending(): gtk.main_iteration()
    os.system(app.getselectedpath())

def hover(app):
    """
    Plugins may use the playlist-area for displaying info, since most plugins
    won't generate items usable for a playlist. So this eventhandler is called
    whenever the curser is on an entry from this plugin
    """
    global info
    slices = os.path.split(app.getselectedpath())
    info.set_label(
        "<span color='#770000' font='monospace 36'>"+
        "╭──────────╮\n"+
        "│ <span color='#ff7300'>External</span> │\n"+
        "╰──────────╯</span>\n\n\n\n"+
        "<span font='monospace 24' color='#666666'>" + slices[0]+ "</span>\n\n"+
        "<span font='monospace 24'>" + slices[1]+ "</span>")
    
    if app.rightframe.get_child() != info:
        app.rightframe.remove(app.rightframe.get_child())
        app.rightframe.add(info)
    

def infiltrate(app):
    """
    This function is called, after the main filetree is build. It has full access
    to gktgui.MainWindow instance, so be careful.
    """
    
    # add treeview-entries, one for each shellscript to root.
    # when generating an entry, see comments below
    shs = os.path.join(app.prefix,"external_scripts.pselect")
    if os.path.exists(shs):
        hacks = []
        f = open(shs)
        for l in f:
            l = l.strip()
            if l.startswith("#"): continue
            l = l.split("\t")
            if len(l) != 2: continue
            piter = app.treestore.append(None, [
                l[0],      # Name
                "",        # Length/Duration. Should be in the format "H:MM:SS" or "MM:SS"
                "ShExec",  # Resolution. May be an arbitrary string.
                "",        # Audiochannels. 
                "",        # Size. May also be something else.
                "Now",     # Modification Time. Or any other string.
                l[1],      # path/URI/URL to something, mplayer can play, if audiochannels are not "X".
                launch,    # an event-handler "row-activate". Gets the app as parameter.
                hover      # an event-handler which get triggerd, when a row gets selected
            ])
        f.close()
