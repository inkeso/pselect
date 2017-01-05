#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, os
import urllib, re
import gtk, gobject, webkit
import threading, time

gobject.threads_init()

from ..libs import widgets

import c3tvparser

IDLE="""<html><head>
  <style>
    * { font-size: 44px; font-family:Tahoma; line-height:52px; background: #151515; color: white; text-align:center; }
    pre { font-family:monospace; font-size: 16px; }
  </style>
</head><body>
  <br/>
  <pre style="color:#ff7300; font-size:36pt; padding:0.5em; border:3pt solid #770000; border-radius:8pt; display: inline-block; margin-top:27pt;">C3TV</pre>
  <br/><br/>
  <img src="file:///"""+sys.path[0]+"""/plugins/c3tv/ccclogo.png" style="display:block;margin:auto;" />
  <br/><br/>
  %s
</body></html>"""


c3tvparser.VIDEOTEMPLATE = """
<html><head>
  <style>
    * {{ font-family:Tahoma; background: #151515; color: white; }}
    body {{ font-size: 24pt; }}
    h1 {{ font-size:32pt; }}
    h2 {{ font-size:28pt; }}
    h3 {{ font-size:24pt; }}
  </style>
</head><body>
  <h1>{h1}</h1>
  <h2>{h2}</h2>
  <h3>{speaker}, {date}, {duration}</h3>
  <div>{about}</div>
</body></html>
"""

class CccInfo():
    def __init__(self):
        self.currentvideourl = None
        self.infoframe = None # the widget containing the info-frame. set in plugin.
        self.mozi = webkit.WebView()
        self.box = gtk.ScrolledWindow()
        self.box.add(self.mozi)
        self.box.show_all()
        self.setIdle()
    
    def _setHtml(self, html, srcuri="file:///"+sys.path[0]):
        self.mozi.load_html_string(html, srcuri)
        while gtk.events_pending(): gtk.main_iteration()
    
    def setMovieInfo(self, link):
        thread = threading.Thread(target=self._movieInfoThread, args=(link,))
        gobject.idle_add(thread.start)
    
    def _movieInfoThread(self, link):
        """
        Retrieve folder- or movieinfos from the net and display them
        (and add items to the tree, if neccessary)
        """
        x = c3tvparser.getItem(link)
        if x and x[0] == "VIDEO":
            gobject.idle_add(self._setHtml, x[1][1])
            self.currentvideourl = x[1][2]
    
    def setIdle(self, msg=""):
        self.currentvideourl = None
        gobject.idle_add(self._setHtml, IDLE % msg)


class CccTree():
    def __init__(self):
        """
        If you want to use this as a plugin, overwrite:
        - self.playback(self, url)
        - self.treestore # gtk.TreeStore
        - self.movielist # gtk.TreeView
        - self.infoframe # gtk.Frame()
        and call self.appendTree()
        """
        self.info = CccInfo()
        self._threads = [] # keeping track of cursor-changes
        self.c3tv = None
    
    def mainwindow(self, size=(800,600), playerCmd="mplayer -fs '%s'"):
        """
        usefull for stand-alone-usage.
        """
        self.playerCmd = playerCmd
        
        columns = ("Name", "Length", "", "", "", "Date", "URL", None, None)
        cTypes  = (str, str, str, str, str, str, str, object, object)
        # you may wonder, why there are this many columns in the tree store.
        # The 3 empty-string- and 2 object-columns are not needed (or used) but
        # keeping them  in places makes it very easy to use this class as a 
        # plugin for Pselect as well as a standalone-GUI.
        
        # Movie list
        self.treestore = gtk.TreeStore(*cTypes) 
        self.movielist = gtk.TreeView()
        self.movielist.set_model(self.treestore)
        # create the TreeViewColumn to display the data
        cell = gtk.CellRendererText()                   # create a CellRenderer
        for cn in (0,1,5):
            one = gtk.TreeViewColumn(columns[cn])  # create column-object
            one.pack_start(cell, cn==0)                 # add cell & allow expansion, if first
            one.add_attribute(cell, 'text', cn)         # retrieve text from corresponding column in treestore
            self.movielist.append_column(one)           # add column to TreeView
            
        self.movielist.set_search_column(0)             # make it searchable
        
        # Create a ScrolledWindow with movielist and add it to a HBox
        self.scrollml = gtk.ScrolledWindow()
        self.scrollml.add(self.movielist)
        self.infoframe = gtk.Frame()
        self.infoframe.add(self.info.box)
        self.hbox = gtk.HBox(spacing=2)
        self.hbox.pack_start(self.scrollml)
        self.hbox.pack_start(self.infoframe)
        
        # Main Window
        self.wind = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.wind.set_title("C3TV")
        global IDLE
        IDLE+="<div style='font-size:10pt;'>Keys: F10 for stream selection Dialog, Esc to quit</div>"
        if type(size) == str and size.lower() == "fullscreen":
            self.wind.maximize();
        elif type(size) in (tuple, list):
            self.wind.set_default_size(*size)
        self.wind.add(self.hbox)
        self.wind.show_all()
        
        # assign event-handlers
        self.wind.connect("destroy", gtk.main_quit) # or on ESC:
        
        self.keys = {
            gtk.keysyms.Escape: gtk.main_quit,
            gtk.keysyms.F10: lambda: self.on_activate(special=True)
        }
        self.movielist.connect("key-press-event", lambda x,y: y.keyval in self.keys and self.keys[y.keyval]() )
        self.movielist.connect("cursor-changed",  self.on_cursor)
        self.movielist.connect("row-activated",   self.on_activate)
        self.appendTree()
        self.movielist.set_cursor(0)
        
        gtk.main()
    
    def appendTree(self, url=None, node=None):
        # if not hasChilds
        self.info.setIdle("Loading media.ccc")
        while gtk.events_pending(): gtk.main_iteration()
        if url is not None: 
            x = c3tvparser.getItem(url)
        else:
            x = c3tvparser.getItem()
        if not x: return # there are some empty dirs
        # Add folders [caption, link]
        if x[0] == "FOLDERS":
            for entry in x[1]:
                self.treestore.append(node, ("📁 "+entry[0], "", "", "", "", "", entry[1], self.on_activate, self.on_cursor))
        # Add videos [caption, link, duration, date, speaker]
        if x[0] == "VIDEOLIST":
            for entry in x[1]:
                if entry[2]: self.treestore.append(node, ("✇ " + entry[0], entry[2], "", "2", "", entry[3], entry[1], self.on_activate, self.on_cursor))
        self.info.setIdle()
    
    def delayedMovieInfo(self):
        time.sleep(.05)
        self._threads.pop()
        if len(self._threads) == 0:
            citer = self.treestore.get_iter(self.movielist.get_cursor()[0])
            self.info.setMovieInfo(self.treestore.get_value(citer, 6))
    
    def on_cursor(self, tv=None):
        # is our info-widget currently displayed in infoframe?
        # this is only useful when used as a plugin.
        if self.infoframe.get_child() != self.info.box:
            self.infoframe.remove(self.infoframe.get_child())
            self.infoframe.add(self.info.box)
        
        while gtk.events_pending(): gtk.main_iteration()
        citer = self.treestore.get_iter(self.movielist.get_cursor()[0])
        film = self.treestore.get_value(citer, 3) == "2"
        if film: 
            # delay fetching movie-info a bit
            thread = threading.Thread(target=self.delayedMovieInfo, args=())
            self._threads.append(thread.getName())
            gobject.idle_add(thread.start)
        else:
            self.info.setIdle()
    
    def playback(self, url):
        """
        Playback URL. May be overwritten, when used as a plugin.
        """
        os.system(self.playerCmd % url)
    
    def on_activate(self, tv=None, sel=None, cColumn=None, special=False):
        tview = self.movielist # our treeview
        tstor = self.treestore # associated treestore
        
        selected = tview.get_cursor()[0]
        citer = tstor.get_iter(selected)
        film = tstor.get_value(citer, 3) == "2"
        url =  tstor.get_value(citer, 6)
        title = tstor.get_value(citer, 0).split(" ", 1)[1]
        if film:
            i = self.info.currentvideourl
            if special: # show selection dialog
                dlgbox = widgets.MirrorDialog(title)
                for m in i.keys(): dlgbox.addOption(m)
                def play(txt): self.playback(i[txt])
                def temp(txt): widgets.Download(i[txt], "/tmp/tempvideofile", self.playback, True, title)
                def save(txt, fina): widgets.Download(i[txt], fina, self.playback, False, title)
                dlgbox.dispatch = {"play": play, "temp": temp, "save": save}
                dlgbox.launch()
            else:
                # prefer mp4 full-hd if available...
                candi = filter(lambda k: "mp4" in k and "full-hd" in k, i.keys())
                if len(candi) < 1: candi = filter(lambda k: "mp4" in k, i.keys())
                if len(candi) < 1: candi = k
                # ...and with the most languages
                mostlangs, vidurl = 0, ""
                for k in candi:
                    langs = len(k.split()[2].split("-"))
                    if langs > mostlangs:
                        mostlangs = langs
                        vidurl = i[k]
                self.playback(vidurl)
        else:
            hasChilds = tstor.iter_has_child(citer)
            isExpanded = tview.row_expanded(selected)
            if not hasChilds:
                self.appendTree(url, citer)
                tview.expand_row(selected, False)
                self.info.setIdle()
            elif "wind" in dir(self): # only if standalone
                if not isExpanded:
                    tview.expand_row(selected, False)
                else:
                    tview.collapse_row(selected)
