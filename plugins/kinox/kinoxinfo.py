#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os, sys
import gtk, gobject, webkit
import threading, time

gobject.threads_init()

import kinoxparser

from ..libs import widgets

# TODO: sys.path[0] ersetzen durch path to current filename
IDLE="""<html><head>
  <style>
    * { font-size: 44px; font-family:Tahoma; line-height:52px; background: #151515; color: white; text-align:center; }
    pre { font-family:monospace; font-size: 22px; }
  </style>
</head><body>
  <img src="file:///"""+sys.path[0]+"""/plugins/kinox/kinox.png" style="display:block;margin:auto;" />
  <br/>
  <pre>%s</pre>
</body></html>"""


VIDEOTEMPLATE = """
<html><head>
  <style>
    * { font-family:Tahoma; background: #151515; color: white; }
    body { font-size: 24pt; }
    h1 { font-size:32pt; }
    .Grahpics    { float:left; width:33%%; margin-right: 1em;}
    .Grahpics img { width:100%%; }
    .Descriptore { float:left;  }
    li { display:block; margin:0.7em; }
    .Director::before { content: "Director: " }
  </style>
</head><body>
  %s
</body></html>
"""

class KinoxInfo():
    def __init__(self):
        self.kinox = kinoxparser.Kinox()
        self.infoframe = None # the widget containing the info-frame. set in plugin.
        self.mozi = webkit.WebView()
        self.box = gtk.ScrolledWindow()
        self.box.add(self.mozi)
        self.box.show_all()
        self.setIdle()
    
    def _setHtml(self, html, srcuri="file:///"+sys.path[0]):
        self.mozi.load_html_string(html, srcuri)
        while gtk.events_pending(): gtk.main_iteration()
    
    def setMovieInfo(self, vidid):
        thread = threading.Thread(target=self._movieInfoThread, args=(vidid,))
        gobject.idle_add(thread.start)
    
    def _movieInfoThread(self, vidid):
        """
        Retrieve folder- or movieinfos from the net and display them
        (and add items to the tree, if neccessary)
        """
        x = self.kinox.getInfo(vidid)
        gobject.idle_add(self._setHtml, VIDEOTEMPLATE % x, self.kinox.URL)
    
    def setIdle(self, msg=""):
        self.currentvideourl = None
        gobject.idle_add(self._setHtml, IDLE % msg)
        while gtk.events_pending(): gtk.main_iteration()

class KinoxGUI():
    def __init__(self):
        """
        If you want to use this as a plugin, overwrite:
        - self.playback(self, url)
        - self.infoframe # gtk.Frame() for the info-widget
        - self.treeview  # gtk.TreeView for displaying the items
        - self.treestore # associated gtk.TreeStore
        and call self.startpopulate()
        
        Otherwise these widgets are created in self.mainwindow()
        """
        self.treeview = None
        self.treestore = None
        self.infoframe = None
        self.info = KinoxInfo()
        
        self._threads = [] # keeping track of cursor-changes
    
    def mainwindow(self, size=(800,600), playerCmd="mplayer -fs '%s'"):
        """
        usefull for stand-alone-usage.
        """
        self.playerCmd = playerCmd
        
        columns = ("Name", "Lang", "", "", "", "", "URL", None, None)
        cTypes  = (str, str, str, str, str, str, str, object, object)
        # you may wonder, why there are this many columns in the tree store.
        # The 4 empty-string- and 2 object-columns are not needed (or used) but
        # keeping them in places makes it very easy to use this class as a 
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
        self.wind.set_title("kinox.to")
        if type(size) == str and size.lower() == "fullscreen":
            self.wind.maximize();
        elif type(size) in (tuple, list):
            self.wind.set_default_size(*size)
        self.wind.add(self.hbox)
        self.wind.show_all()
        
        # assign event-handlers
        self.wind.connect("destroy", gtk.main_quit) # or on ESC:
        self.movielist.connect("key-press-event", self.on_keypressed)
        self.movielist.connect("cursor-changed",  self.on_cursor)
        self.movielist.connect("row-activated",   self.on_activate)
        self.appendTree()
        self.movielist.set_cursor(0)
        gtk.main()
   
    def appendTree(self, kxentry=None, node=None):
        if kxentry is None: # init
            self.treestore.append(node, ("Search","", "", "", "", "", "", self.on_activate, self.on_cursor))
            self.treestore.append(node, ("Latest","", "", "", "", "", "", self.on_activate, self.on_cursor))
            self.treestore.append(node, ("Popular","", "", "", "", "", "", self.on_activate, self.on_cursor))
        else:
            for l in kxentry:
                self.treestore.append(node, (l[1], l[0], "", "", "", "", l[2], self.on_activate, self.on_cursor))
        
        self.info.setIdle()
    
    def getText(self, caption=""):
        #base this on a message dialog
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            #gtk.BUTTONS_OK_CANCEL,
            gtk.BUTTONS_NONE,
            None)
        dialog.set_markup(caption)
        entry = gtk.Entry()
        entry.connect("activate", lambda x: dialog.response(gtk.RESPONSE_OK))
        dialog.vbox.pack_end(entry, True, True, 0)
        dialog.show_all()
        text = None
        if dialog.run() == gtk.RESPONSE_OK:
            text = entry.get_text()
        dialog.destroy()
        return text
    
    def on_activate(self, tv=None, selected=None, cColumn=None, special=False):
        tview = self.movielist # our treeview
        tstor = self.treestore # associated treestore
        
        selected = tview.get_cursor()[0]
        citer = tstor.get_iter(selected)
        
        vidid = tstor.get_value(citer, 6)
        if vidid:
            if special:
                self.special(vidid)
            else:
                lnk = self.info.kinox.getStream(vidid, self.info.setIdle)
                if lnk: 
                    self.info.setIdle("playback "+lnk)
                    self.playback(lnk)
                    self.info.setMovieInfo(vidid)
        else:
            sup = tstor.get_value(citer, 0)
            if sup == "Search":
                txt = self.getText("Was suchen wir denn?")
                if txt:
                    # remove childs from treestore
                    fc = tstor.iter_children(citer)
                    while fc is not None:
                        tstor.remove(fc)
                        fc = tstor.iter_children(citer)
                    
                    # add search-results
                    self.appendTree(self.info.kinox.search(txt), citer)
                    tview.expand_row(selected, False)
            else:
                if not tstor.iter_has_child(citer):
                    self.appendTree(self.info.kinox.search(sup), citer)
                    tview.expand_row(selected, False)
                elif "wind" in dir(self): # only if standalone
                    if not tview.row_expanded(selected):
                        tview.expand_row(selected, False)
                    else:
                        tview.collapse_row(selected)
    
    def on_keypressed(self, win, evt):
        """
        only used by self.mainwindow(): bind keyboard-shortcuts
        """
        if evt.keyval == gtk.keysyms.F10:
            self.on_activate(special=True)
            
        if evt.keyval == gtk.keysyms.Escape:
            gtk.main_quit()
    
    def special(self, vidid):
        """
        Special action:
        Select mirror to 
         - play
         - download to tmp & play on demand
         - download to dir
        
        """
        mir = self.info.kinox.getMirros(vidid)
        dlgbox = widgets.MirrorDialog(vidid)
        
        for m in kinoxparser.HosterRank:
            if m not in mir: continue
            if m not in kinoxparser.ValidHosters:
                dlgbox.mirrortab.pack_start(gtk.Label(m + ": unknown Hoster-ID"))
            else:
                hostername = kinoxparser.ValidHosters[m]
                if kinoxparser.streamhoster.checkParser(hostername):
                    dlgbox.addOption("%s: %s" % (m, hostername))
                else:
                    dlgbox.mirrortab.pack_start(gtk.Label("%s: %s (unsupported)" % (m, hostername)))

        def play(txt):
            lnk = self.info.kinox.getStream(vidid, self.info.setIdle, [txt.split(":")[0]])
            if lnk:
                self.info.setIdle("play "+lnk)
                self.playback(lnk)
                    
        def temp(txt):
            lnk = self.info.kinox.getStream(vidid, self.info.setIdle, [txt.split(":")[0]])
            if lnk:
                self.info.setIdle("download \n"+lnk+"\n to tmp")
                widgets.Download(lnk, "/tmp/tempvideofile", self.playback, True, vidid)
        def save(txt, fina):
            lnk = self.info.kinox.getStream(vidid, self.info.setIdle, [txt.split(":")[0]])
            ext = lnk.rsplit(".",1)[1]
            if len(ext) > 4: ext=".mp4" # this is kind of a bad thing
            fina = fina+"."+ext
            self.info.setIdle("download \n"+lnk+"\n to \n"+fina)
            widgets.Download(lnk, fina, self.playback, False, vidid)
        
        dlgbox.dispatch = {"play": play, "temp": temp, "save": save}
        dlgbox.launch()
        self.info.setMovieInfo(vidid)
        return True
    
    def playback(self, url):
        """
        Playback URL. May be overwritten, when used as a plugin.
        """
        os.system(self.playerCmd % url)
    
    def on_cursor(self, tv=None):
        # is our info-widget currently displayed in infoframe?
        # this is only useful when used as a plugin.
        if self.infoframe.get_child() != self.info.box:
            self.infoframe.remove(self.infoframe.get_child())
            self.infoframe.add(self.info.box)
        
        while gtk.events_pending(): gtk.main_iteration()
        citer = self.treestore.get_iter(self.movielist.get_cursor()[0])
        vidid = self.treestore.get_value(citer, 6)
        if vidid:
            # delay fetching movie-info a bit (because of scrolling)
            thread = threading.Thread(target=self.delayedMovieInfo, args=())
            self._threads.append(thread.getName())
            gobject.idle_add(thread.start)
        else:
            self.info.setIdle()
    
    def delayedMovieInfo(self):
        time.sleep(.25)
        self._threads.pop()
        if len(self._threads) == 0:
            citer = self.treestore.get_iter(self.movielist.get_cursor()[0])
            self.info.setMovieInfo(self.treestore.get_value(citer, 6))
