#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This is a plugin for mounting/unmounting additional devices and refreshing
the filetree.
The mountpoint of the device should be already in it. Empty Folders are not
shown, so it will be hidden if the device is not mounted.
"""


# TODO: special action: anstehendes kommando (mount/unmount) vorher bearbeiten


import os, re, time, gtk
import pvid

# initialize custiom widget(s) for this plugin
info = gtk.Label("Mount")
info.set_use_markup(True)
info.set_justify(gtk.JUSTIFY_CENTER)
info.set_alignment(0.5, 0.125)
info.set_line_wrap(True)
info.mounted = {} # yes, we misuse this widget to store additional stuff
info.show()

def launch(app):
    """
    Eventhandler for activating an entry, generated below. (Hitting "Enter")
    """
    global info

    if app.getselectedresolution() == "Mount":
        cmd, suc = app.getselectedpath(), "Unmount"
    else:
        cmd, suc = app.getselectedmtime(), "Mount"
    
    info.set_label(cmd)
    while gtk.events_pending(): gtk.main_iteration()
    print cmd
    if os.system(cmd) == 0: # success yaay!
        citer = app.treestore.get_iter(app.treeview.get_cursor()[0])
        app.treestore.set_value(citer, 2, suc)
        info.set_label("Reloading filelist...")
        while gtk.events_pending(): gtk.main_iteration()
        app.repopulate()
    hover_main(app)


def hover_main(app):
    """
    Plugins may use the playlist-area for displaying info, since most plugins
    won't generate items usable for a playlist. So this eventhandler is called
    whenever the cursor is on an entry from this plugin.
    This plugin could, however, generate playlistable entries. but since we don't
    scan the new files for metadata such as playtime (because it would probably
    take long) we hide the playlists nonetheless.
    """
    global info
    if app.getselectedresolution() == "Mount":
        cmd = app.getselectedpath()
    else:
        cmd = app.getselectedmtime()
    info.set_label(
        "<span color='#770000' font='monospace 36'>"+
        "╭───────────────────────╮\n"+
        "│ <span color='#ff7300'>Mount External Device</span> │\n"+
        "╰───────────────────────╯</span>\n\n\n\n"+
        "<span font-weight='bold'>" + app.getselectedresolution() + "</span>\n\n"+
        "<span>" + cmd + "</span>")
    
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
    shs = os.path.join(app.prefix,"additional_devices.pselect")
    if os.path.exists(shs):
        f = open(shs)
        for l in f:
            l = l.strip()
            if l.startswith("#"): continue
            l = l.split("\t")
            if len(l) != 3:
                continue
            piter = app.treestore.append(None, [
                l[0],      # Name.
                "",        # Length/Duration. Should be in the format "H:MM:SS" or "MM:SS"
                "Mount",   # Resolution. May be an arbitrary string.
                "",        # Audiochannels
                "",        # Size. May also be something else. Here: Mountpoint
                l[2],      # Modification Time. Or any other string. Here: full unmountcommand
                l[1],      # path/URI/URL to something, mplayer can play. Or something else,
                           # if you replace "row-activate" function. In this case: full mountcommand.
                launch,    # an event-handler "row-activate". Gets the app as parameter.
                hover_main # an event-handler which get triggerd, when a row gets selected
            ])
        f.close()
