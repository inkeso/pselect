#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
This is an example plugin, adding a clock
"""

import time, gtk, gobject, pango

# Dirty globals
app = None
lab = None

# update clock
def clocky():
    global app, lab
    tic = time.time()
    fmt = "<span color='#999'>It's now:</span> %H:%M "
    toc = 0
    try:
        lz = app.getselectedtime().split(":")
        if len(lz) == 2:
            toc = int(lz[0])*60 + int(lz[1])
        elif len(lz) == 3:
            if "days" in lz[0]:
                dh = lz[0].split(" days, ")
                toc = int(dh[0])*60*60*24 + int(dh[1])*60*60 + int(lz[1])*60 + int(lz[2])
            else:
                toc = int(lz[0])*60*60 + int(lz[1])*60 + int(lz[2])
    except:
        print lz
    if toc > 0:
        fmtx = "<span color='#999'>Finish:</span>"
        fmt = fmtx + " %H:%M "
    if toc > 60*60*24:
        fmt = fmtx + " %a, %H:%M "
    if toc > 60*60*24*6:
        fmt = fmtx + " %a, %d. %h. %H:%M "
    if toc > 60*60*24*365:
        fmt = "<span color='#F77'>Over a year!</span>"
    tic += toc
    lab.set_label(time.strftime(fmt, time.localtime(tic)))
    return True


def newselectedhover(void=None):
    global app
    clocky()
    app.selectedhover()

def infiltrate(ap):
    """
    This function is called, after the main filetree is build. It has full access
    to gktgui.MainWindow instance, so be careful.
    """
    global app, lab
    app = ap
    
    # rearrange filter-box
    app.midvbox.remove(app.filterframe)
    app.filterframe.remove(app.filterentry)
    lab = gtk.Label(time.strftime(" %H:%M:%S ")) # system-clock
    lab.modify_font(pango.FontDescription("monospace"))
    lab.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(30535,35535,20000))
    lab.set_use_markup(True)
    hbox = gtk.HBox()
    hbox.pack_start(lab, expand=False)
    hbox.pack_start(app.filterentry)
    hbox.set_border_width(4)
    evbox = gtk.EventBox()
    evbox.add(hbox)
    evbox.show_all()
    app.midvbox.pack_start(evbox)
    
    gobject.timeout_add(1000, clocky)
    app.treeview.connect("cursor-changed", newselectedhover)
    
