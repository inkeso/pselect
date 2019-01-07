#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  gtkgui.py
#  
#  Copyright 2014 Eloi Maelzer <iks@SteroiX>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

'''
This is the GTK-GUI for pselect. It consists of two panes. One for the
file-list and (optionally) one for up to 4 playlists.
'''

import time, os, sys, subprocess
import gtk, gobject
import pvid

# import all plugins. This feels wrong. There must be a way to import all of them
# automagically. I tried pkgutil but didn't succeed.
import plugins.pregui
import plugins.bsto
import plugins.c3tv
import plugins.clocky
import plugins.kinox
import plugins.mountdev
import plugins.playlisthide
import plugins.shexec

# Suppress GTK-Warnings. *sigh*
import warnings
warnings.simplefilter('ignore', Warning)

gobject.threads_init()

# Keyboard Shortcuts:
# 1 - Add complete to PL 1
# 2 - Add snippet to PL 1
# 3 - Focus PL 1
# 4,5,6 same for PL 2
# 7,8,9 for PL 3
# *,0,# for PL 4 (* and # will be remapped for LIRC)
# Del - remove currently highlighted video from active playlist (see below)
# F10 - Play all playlists / Execute special action from plugin
# F9 - Focus main filelist
# [Return] Play selected Item

class MainWindow():
    def __init__(self, vpath, autostart=lambda: None, clearcache=False, plugs=[], fullscreen=False):
        # player & parameters for preview / row-activate. may be modified later.
        # default to mplayer. omxplayer works as well. nothing else ATM.
        self.player = "mplayer"
        self.parameters = ""
        self.ch6filter = ""
        self.ch2filter = ""
        self.autostart = autostart
        self.clearcache = clearcache
        self.prefix = vpath
        
        # Create Main Window
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win.set_title("pSelect GUI")
        if fullscreen:
            self.win.set_decorated(False)
            self.win.maximize()
        
        # Create TreeView in a ScrolledWindow
        self.scrollview = gtk.ScrolledWindow()
        self.scrollview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.treeview = gtk.TreeView()
        # NA == Number of Audiochannels in Video.
        # This is also used to hack a different function:
        columns = ("File", "Duration", "Resolution", "NA", "Size", "Date", "fullPath", "PluginRowActivate", "PluginRowHover")
        ctypes  = (str,) * (len(columns)-2) + (object, object)
        self.treestore = gtk.TreeStore(*ctypes)
        self.treeview.set_model(self.treestore)
        #  TreeViewColumns to display the data
        cell = gtk.CellRendererText()
        for i in range(len(columns)-2):
            one = gtk.TreeViewColumn(columns[i])
            one.pack_start(cell, i==0)
            one.set_resizable(True)
            one.add_attribute(cell, "text", i)
            self.treeview.append_column(one)
        self.treeview.set_headers_visible(True)
        self.treeview.set_search_column(0)
        self.scrollview.add(self.treeview)
        
        # tree is created. load videos
        self.rootiters = []
        self.repopulate()
        
        # lower area widgets (middle / left)
        self.midvbox = gtk.VBox(spacing=3)
        
        # filter
        self.filterframe = gtk.Frame("Filter")
        self.filterentry = gtk.Entry()
        self.filterframe.add(self.filterentry)
        
        # group "after playlists end"
        self.postframe = gtk.Frame("After playlists end")
        self.postbox1 = gtk.HBox(spacing=3)
        self.postcheckbox = gtk.CheckButton("Execute command:")
        self.postentry = gtk.Entry()
        self.postbox1.pack_start(self.postcheckbox, expand=False)
        self.postbox1.pack_start(self.postentry, expand=True)
        self.postbox2 = gtk.HBox(spacing=3)
        self.postcleanup = gtk.CheckButton("Delete playlists")
        self.exitcheckbox = gtk.CheckButton("Exit program")
        self.postbox2.pack_start(self.postcleanup, expand=False)
        self.postbox2.pack_start(self.exitcheckbox, expand=False)
        self.postvbox = gtk.VBox()
        self.postvbox.pack_start(self.postbox1)
        self.postvbox.pack_start(self.postbox2)
        self.postframe.add(self.postvbox)
        
        self.midvbox.pack_start(self.filterframe)
        self.midvbox.pack_start(self.postframe)
        
        # lower area widgets (far right, action-buttons)
        self.actionvbox = gtk.VButtonBox()
        self.actionvbox.set_layout(gtk.BUTTONBOX_SPREAD)
        self.specialbutton = gtk.Button(label="Action")
        self.quitbutton = gtk.Button(stock=gtk.STOCK_QUIT)
        self.actionvbox.pack_start(self.specialbutton)
        self.actionvbox.pack_start(self.quitbutton)
        
        # Pack lower area
        self.lowerhbox = gtk.HBox(spacing=3)
        self.lowerhbox.pack_start(self.midvbox, expand=True)
        self.lowerhbox.pack_start(self.actionvbox, expand=False)
        
        # Create Playlists, pack them in resizable Panes
        self.playlists = [PlaylistWidget(i+1, self) for i in range(4)]
        self.pltab = gtk.VPaned()
        self.pltab_t = gtk.HPaned()
        self.pltab_b = gtk.HPaned()
        self.pltab.pack1(self.pltab_t)
        self.pltab.pack2(self.pltab_b)
        
        self.pltab_t.pack1(self.playlists[0].widget)
        self.pltab_t.pack2(self.playlists[1].widget)
        self.pltab_b.pack1(self.playlists[2].widget)
        self.pltab_b.pack2(self.playlists[3].widget)

        # Pack main window
        self.lvbox = gtk.VBox()
        self.lvbox.pack_start(self.scrollview, expand=True)
        self.lvbox.pack_start(self.lowerhbox, expand=False)
        
        self.leftframe = gtk.Frame()
        self.leftframe.add(self.lvbox)
        self.rightframe = gtk.Frame()
        self.rightframe.add(self.pltab)
        
        self.mainhpan = gtk.HPaned()
        self.mainhpan.pack1(self.leftframe)
        self.mainhpan.pack2(self.rightframe)
        self.win.add(self.mainhpan)
        
        # assign eventhandlers
        self.win.connect("delete_event", gtk.main_quit)
        self.win.connect("key_press_event", self.global_keypressed)
        self.asid = self.mainhpan.connect("expose-event", self.startonce)
        self.treeview.connect("key_press_event", self.list_keypressed)
        self.treeview.connect("row_activated", self.row_activated)
        self.treeview.connect("cursor-changed", self.selectedhover)
        self.quitbutton.connect("clicked", gtk.main_quit)
        self.specialbutton.connect("clicked", lambda x: self.selectedhandler(special=True))
        self.filterentry.connect("changed", self.filterchanged)
        
        # load plugins
        print "Plugins:", 
        for plug in plugs:
            print plug,
            eval("plugins."+plug).infiltrate(self)
        print
        # und in der infiltrate-funktion kann denn schön alles umgehäkelt werden.
        # Das ist super-scheiße, weil ein plugin ein anderes kaputt machen kann
        # und man aufpassen muss, daß die plugins nicht wechselwirken. But YOLO.

        self.win.show_all()
        self.treeview.grab_focus()
        self.isfiltered = False
    
    def startonce(self, wi, ev):
        '''
        workaround for resizing gtk.Paned after showing the window
        this may be overwritten in a launcher
        '''
        self.mainhpan.disconnect(self.asid)
        while gtk.events_pending(): gtk.main_iteration()
        self.autostart()
        self.treeview.set_cursor(0)
        self.treeview.grab_focus()
    
    def repopulate(self):
        self.deltree()
        self.videos = pvid.Videos(self.prefix, clearcache=self.clearcache)
        self.addtotree(self.videos.files)
    
    def addtotree(self, branch, root=None):
        '''
        add pvid-entries to gtk.Treeview (recursive)
        store them, so we can remove them later
        '''
        for leaf in reversed(branch):
            dim = ""
            nom = leaf["fileName"]
            if "dim" in leaf: # file
                dim = "%d x %d" % leaf["dim"]
                try: nom = nom[:nom.rindex(".")]
                except: pass
            elif leaf["files"] > 0: # dir
                dim = "%d files" % leaf["files"]
            
            piter = self.treestore.prepend(root, [
                nom,
                pvid.sec2hms(leaf["vLen"]) if leaf["vLen"] > 0 else "",
                dim,
                leaf["aCh"] if "aCh" in leaf else "",
                pvid.byte2hr(leaf["size"]) if leaf["size"] > 0 else "",
                time.strftime("%d %b %Y %H:%M", time.gmtime(leaf["mTime"])),
                leaf["fullPath"],
                self.playlocal,
                self.hoverlocal
            ])
            if root is None: self.rootiters.insert(0, piter)
            if "items" in leaf: self.addtotree(leaf["items"], piter)
    
    def deltree(self):
        for i in self.rootiters: self.treestore.remove(i)
        self.rootiters = []
    
    def mplayer(self, filename):
        """
        launch mplayer with correct parameters
        """
        parameters = ""
        a = self.getselectedaudio()
        if a == "6": parameters += self.ch6filter
        if a == "2": parameters += self.ch2filter
        pvid.play(filename, self.parameters + " " + parameters, player=self.player)

    def playlocal(self, void=None, special=False):
        if special:
            self.playall()
        else:
            citer = self.treestore.get_iter(self.treeview.get_cursor()[0])
            if not self.treestore.iter_has_child(citer):
                self.mplayer(self.getselectedpath())
    
    def hoverlocal(self, void=None):
        # (re)assign playlist to HPaned (may be removed by a plugin)
        if self.rightframe.get_child() != self.pltab:
            self.rightframe.remove(self.rightframe.get_child())
            self.rightframe.add(self.pltab)
    
    # Eventhandler for main treeview / filelist
    def row_activated(self, tv, selected, cColumn): # "Enter"
        citer = self.treestore.get_iter(selected)
        if self.treestore.iter_has_child(citer):
            if not tv.row_expanded(selected):
                tv.expand_row(selected, False)
            else:
                tv.collapse_row(selected)
        self.selectedhandler()
    
    def list_keypressed(self, win, evt):
        codes = {
            ord("1"): lambda: self.playlists[0].addtoplaylist(),
            ord("2"): lambda: self.playlists[0].addsniptoplaylist(),
            ord("4"): lambda: self.playlists[1].addtoplaylist(),
            ord("5"): lambda: self.playlists[1].addsniptoplaylist(),
            ord("7"): lambda: self.playlists[2].addtoplaylist(),
            ord("8"): lambda: self.playlists[2].addsniptoplaylist(),
            ord("*"): lambda: self.playlists[3].addtoplaylist(),
            ord("0"): lambda: self.playlists[3].addsniptoplaylist()
        }
        if evt.keyval in codes:
            codes[evt.keyval]()
            return True
        else:
            return False
    
    # Global keyboard shortcuts. F1 to F8 may be used by plugins.
    # TODO: Think of a better way to use one plugin-wide key only.
    def global_keypressed(self, win, evt):
        codes = {
            ord("3"):    self.playlists[0].treeview.grab_focus,
            ord("6"):    self.playlists[1].treeview.grab_focus,
            ord("9"):    self.playlists[2].treeview.grab_focus,
            ord("#"):    self.playlists[3].treeview.grab_focus,
            gtk.keysyms.F9     : self.treeview.grab_focus,
            gtk.keysyms.F10    : lambda: self.selectedhandler(special=True),
            gtk.keysyms.Escape : gtk.main_quit
        }
        if evt.keyval in codes:
            codes[evt.keyval]()
            return True
        else:
            return False
    
    def getselectedcolumn(self, n):
        return self.treestore.get_value(self.treestore.get_iter(self.treeview.get_cursor()[0]),n)
    
    def getselectedname(self): return self.getselectedcolumn(0)
    def getselectedtime(self): return self.getselectedcolumn(1)
    def getselectedresolution(self): return self.getselectedcolumn(2)
    def getselectedaudio(self): return self.getselectedcolumn(3)
    def getselectedsize(self): return self.getselectedcolumn(4)
    def getselectedmtime(self): return self.getselectedcolumn(5)
    def getselectedpath(self): return self.getselectedcolumn(6)
    
    def selectedhandler(self, special=False):
        handler = self.getselectedcolumn(7)
        if handler:
            if special:
                if "special" in handler.__code__.co_varnames:
                    handler(self, special=True)
            else:
                handler(self)
    
    def selectedhover(self, void=None):
        handler = None
        if self.treeview.get_cursor()[0]:
            handler = self.getselectedcolumn(8)
        if handler: handler(self)
    
    def playall(self):
        PRX = "/tmp/pselect.%d." % os.getpid()
        plfiles = [self.playlists[i].playlist.writeplaylist(PRX+"%d" % (i+1), player=self.player) for i in range(4)]
        pvid.multiplay(plfiles, PRX+"master", start=False)
        with open(PRX+"master", 'a') as f:
            if self.postcheckbox.get_active() and len(self.postentry.get_text()) > 0:
                f.write(self.postentry.get_text()+'\n')
        pvid.log("Starting "+PRX+"master")
        subprocess.call(['bash', PRX+"master"])
        # Cleanup?
        if self.postcleanup.get_active():
            [os.unlink(i) for i in plfiles if i is not None]
            os.unlink(PRX+"master")
        if self.exitcheckbox.get_active(): gtk.main_quit()
    
    def filterchanged(self, void):
        """TODO: Filtern macht den treeview kaputt. Außerdem kann das ruhig in ein Plugin"""
        txt = self.filterentry.get_text().upper()
        if len(txt) > 2:
            self.treestore.clear()
            nuc = filter(lambda x: txt in x.upper(), self.videos.cache.keys())
            # {"full/path/to.avi" : {'ID_LENGTH': 1220.0, 'ID_VIDEO_WIDTH': 320, ...}
            for n in nuc:
                #("File", "Duration", "Resolution", "NA", "Size", "Date", "fullPath", "PluginRowActivate", "PluginRowHover")
                piter = self.treestore.prepend(None, [
                    n[len(self.prefix)+1:],
                    pvid.sec2hms(self.videos.cache[n]["ID_LENGTH"]),
                    "%d x %d" % (self.videos.cache[n]["ID_VIDEO_WIDTH"],self.videos.cache[n]["ID_VIDEO_HEIGHT"]),
                    "%d" % self.videos.cache[n]["ID_AUDIO_NCH"],
                    "","", n, self.playlocal, self.hoverlocal
                ])

            self.filterframe.set_label("Filter (%d files)" % len(nuc))
            self.isfiltered = True
        else:
            if self.isfiltered:
                self.treestore.clear()
                self.addtotree(self.videos.files)
                self.filterframe.set_label("Filter")
                self.isfiltered = False


class PlaylistWidget:
    def __init__(self, i, parent):
        # Create TreeView in a ScrolledWindow
        self.i = i # our number
        self.playlist = pvid.Playlist() # playlist-object
        self.parent = parent
        self.parameters = "" # mplayer-parameters to use when a row is activated (preview)
        
       
        # Scrolled TreeView Widget
        self.scrollview = gtk.ScrolledWindow()
        self.scrollview.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.treeview = gtk.TreeView()
        columns = ("File", "Start", "Length", "fullPath")
        ctypes  = (str,) * len(columns)
        self.treestore = gtk.ListStore(*ctypes)
        self.treeview.set_model(self.treestore)
        #  TreeViewColumns to display the data
        cell = gtk.CellRendererText()
        for i in range(len(columns)-1):
            one = gtk.TreeViewColumn(columns[i])
            one.pack_start(cell, i==0)
            one.set_resizable(True)
            one.add_attribute(cell, "text", i)
            self.treeview.append_column(one)
        self.treeview.set_headers_visible(True)
        self.treeview.set_search_column(0)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.treeview.set_reorderable(True)
        self.treeview.connect("key_press_event", self.list_keypressed)
        self.treeview.connect("row_activated", self.row_activated)
        self.treeview.connect("drag_end", self.rows_reordered)
        self.scrollview.add(self.treeview)
        
        # Status-Label
        self.status = gtk.Label()
        self.status.set_text("Playlist %d: 00:00" % self.i)
        
        # Buttons (add)
        self.buttons = gtk.HButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_SPREAD)
        self.addallbtn = gtk.Button("Add All to PL %d" % self.i)
        self.addsnpbtn = gtk.Button("Add snippet to PL %d" % self.i)
        self.addallbtn.connect("clicked", self.addtoplaylist)
        self.addsnpbtn.connect("clicked", self.addsniptoplaylist)
        self.buttons.pack_start(self.addallbtn)
        self.buttons.pack_start(self.addsnpbtn)
        
        # pack everything together
        self.vbox = gtk.VBox(spacing=2)
        self.vbox.pack_start(self.status, expand=False)
        self.vbox.pack_start(self.scrollview, expand=True)
        self.vbox.pack_start(self.buttons, expand=False)
        
        self.widget = gtk.Frame()
        self.widget.add(self.vbox)

    
    def row_activated(self, tv, selected, cColumn): # "Enter"
        sindex = self.treeview.get_cursor()[0][0]
        pitem = self.playlist.playlist[sindex]
        pvid.play(pitem[0], self.parameters, pitem[1], pitem[2], self.parent.player)
    
    def list_keypressed(self, win, evt):
        codes = {
            65535: self.removehighlighted  # [DEL]
        }
        # print "List KeyPressed:", evt.keyval
        if evt.keyval in codes:
            codes[evt.keyval]()
            return True
        else:
            return False
    
    def removehighlighted(self):
        onesel = [x[0] for x in self.treeview.get_selection().get_selected_rows()[1]]
        onesel.sort(reverse=True)
        for i in onesel: self.playlist.playlist.pop(i)
        self.update()
    
    def rows_reordered(self, widg, drag):
        # TODO: treestore to playlist (aka reorder by index)
        newpl = []
        def ts2pl(model, path, itr):
            ff = self.treestore.get_value(itr, 3)
            st = pvid.hms2sec(self.treestore.get_value(itr, 1))
            et = pvid.hms2sec(self.treestore.get_value(itr, 2))
            row = [
                ff,
                -1 if st == 0 else st,
                -1 if et == self.parent.videos.cache[ff]['ID_LENGTH'] else et
            ]
            newpl.append(row)
            return False
        self.treestore.foreach(ts2pl)
        self.playlist.playlist = newpl
        self.update()
    
    def update(self):
        '''update status-label and transport playlist --> TreeView'''
        # map self.playlist.playlist to treeview.
        self.treestore.clear()
        plsum = 0
        for item in self.playlist.playlist:
            start = 0
            if item[1] > 0: start = item[1]
            vlen = self.parent.videos.cache[item[0]]["ID_LENGTH"]
            if item[2] > 0: vlen = item[2]
            entry = [item[0][len(self.parent.prefix)+1:], pvid.sec2hms(start), pvid.sec2hms(vlen), item[0]]
            plsum += vlen
            self.treestore.append(entry)
        self.status.set_text("Playlist %d: %s" % (self.i, pvid.sec2hms(plsum)))
    
    def addtoplaylist(self, ev=None):
        '''
        add selected file or folder to playlist.
        n can be a Button-object with a single digit in its label on last position
        OR an integer (zero-based) playlistnumber
        '''
        
        files = self.parent.videos.getAll(self.parent.getselectedpath())
        
        for k in files: 
            fp = ""
            if k[3] in (1, 2): fp = self.parent.ch2filter
            if k[3] == 6: fp = self.parent.ch6filter
            self.playlist.additem(k[0], parameters=fp)
        self.update()
    
    def addsniptoplaylist(self, ev=None):
        '''
        add a snippet of a selected file or folder to playlist n.
        n can be a Button-object with a single digit in its label on last position
        OR an integer (zero-based) playlistnumber
        '''
        # TODO: From parent-config / GUI
        sublen = 3 * 60
        totlen = 30* 60
        # omxplayer doesn't support playlists and cutting, so add only 1 snipet
        if 'omxplayer' in self.parent.player: totlen = sublen
        files = self.parent.videos.getRandom(self.parent.getselectedpath(), sublen, totlen)

        for k in files: 
            fp = ""
            if k[3] in (1, 2): fp = self.parent.ch2filter
            if k[3] == 6: fp = self.parent.ch6filter
            self.playlist.additem(k[0], k[1], k[2], fp)
        self.update()


