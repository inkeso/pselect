#!/usr/bin/env python2
# -*- coding: utf-8 -*-

########################################################################
# EMBEDDED-Config.
# 
# Hotkeys (1 & 2 stay the same, 3 = special action (instead of F10)
# TODO: delete playlist?
########################################################################

# set custom gtk-theme
import os, sys, subprocess, time
os.environ["GTK2_RC_FILES"]=os.path.join(sys.path[0],"gtkrc/gtk_dark_large_ambiance")

import gtkgui

plugins = ('pregui', 'mountdev', 'bsto', 'kinox', 'c3tv')

def plreplace(app):
    # remove quitbutton etc.
    app.lvbox.remove(app.lowerhbox)
    # hide all other columns
    for i in range(1,7): app.treeview.get_column(i).set_visible(False)
    # create infopanel
    app.meta = gtkgui.gtk.Label()
    app.meta.show_all()
    app.meta.set_padding(5, 5)
    app.meta.set_alignment(0, 0)
    app.meta.set_use_markup(True)
    # remove 2 playlists
    app.pltab_t.remove(app.playlists[0].widget)
    app.pltab.remove(app.pltab_t)
    app.pltab.remove(app.pltab_b)
    # substitute 3rd by infopanel
    app.pltab.pack1(app.meta)
    app.pltab.pack2(app.playlists[0].widget)
    # set Defaults (delete playlist-file after playback)
    app.postcleanup.set_active(False) # Debug=False, Production=True

gtkgui.plugins.pregui.infiltrate = plreplace
app = gtkgui.MainWindow(os.path.join(sys.path[0],"videos"), autostart=lambda: app.mainhpan.set_position(1000), plugs=plugins, fullscreen=True)

def hoverlocal(self, void=None):
    # (re)assign playlist to HPaned (may be removed by a plugin)
    if self.rightframe.get_child() != self.pltab:
        self.rightframe.remove(self.rightframe.get_child())
        self.rightframe.add(self.pltab)
    subpath = self.getselectedpath().replace(self.prefix+"/","")
    subdir = ""
    for s in enumerate(subpath.split("/")[:-1]):
        subdir += "<tt>"+(" "*(12+s[0]))+"└</tt> "+s[1]+"\n"
    
    cp = self.getselectedpath()
    self.meta.set_label("<span weight='bold' size='large'>"+self.getselectedname()+"</span>\n\n" +
        "<tt><b>Time:       </b></tt>"+self.getselectedtime()+"\n"+
        "<tt><b>Resolution: </b></tt>"+self.getselectedresolution()+"\n"+
        "<tt><b>Filesize:   </b></tt>"+self.getselectedsize()+"\n"+
        "<tt><b>Modified:   </b></tt>"+self.getselectedmtime()+"\n"+
        "<tt><b>Path:       </b></tt>"+self.prefix+"\n"+subdir)

# we have to reassign the hover-function-pointer in each treeview-item.
# OR we can use black magic to replace the function-body of the original memberfunction
# and keep the function-pointers intact.
app.hoverlocal.im_func.func_code = hoverlocal.func_code
app.hoverlocal() # *Cough*

# we overwrite this function because it is called on key "3" and we want action
# (F10) instead. It's probably not the best idea to do it this way...
app.playlists[0].treeview.grab_focus = lambda: app.selectedhandler(special=True)

app.parameters = "-o local -b"
app.player = "urxvt -e omxplayer" # *must* be started in a seperate terminal,
app.playlists[0].parameters = app.parameters
app.playlists[0].playlist.parameters = app.parameters

# here we go
gtkgui.gtk.main()

