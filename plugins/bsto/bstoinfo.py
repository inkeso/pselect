#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import bspconfig
import os, sys
import gtk
import streamsite

from ..libs import widgets

SPLORT = "\t──══──\t" # magic string used as a divider

class Bsto():
    FavFile = os.path.join(sys.path[0], bspconfig.favorites)
    
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
        
        # create info-widget
        self.scrolledwindow2 = gtk.ScrolledWindow()
        self.viewport2 = gtk.Viewport()
        self.description = gtk.Label()
        self.description.set_padding(5, 5)
        self.description.set_use_markup(True)
        self.viewport2.add(self.description)
        self.scrolledwindow2.add(self.viewport2)
        self.scrolledwindow2.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scrolledwindow2.show_all()
       
        # last viewed series & favorites (created in self.loadstate()):
        self.lastviewed = ["","",""]
        self.lastbyseries = {}
        self.favorites = []
        #
        
        # created in self.startpopulate():
        self.faviter = None 
        # created in self.populate()
        self.series = None
        
        self.loadstate()
        self.resetlabel()
    
    def xc(self, n, c):
        """
        Helper-function to return a treestore-entry without typing so much
        [n=Name, unused, unused, Audiochannels (unused), 
        Type (Genre, Serie, Seanson or Episode), unused, 
        row-activated-eventhandler, cursor-changed-eventhandler]
        """
        return [n, "", "", "2", c, "", "", self.on_activate, self.on_cursor]
    
    def gettyp(self, selected=None):
        """
        get currently selected type-string (column 4) from tree
        """
        if selected is None:
            selected = self.treeview.get_cursor()[0]
        return self.treestore.get_value(self.treestore.get_iter(selected),4)
    
    def getname(self, selected=None):
        """
        get currently selected name-string (column 0) from tree
        """
        if selected is None:
            selected = self.treeview.get_cursor()[0]
        return self.treestore.get_value(self.treestore.get_iter(selected),0)
    
    #~ # iterate from toplevel to current. (Clear but long)
    #~ def getseriespath(self):
        #~ c = self.treeview.get_cursor()[0]
        #~ it = []
        #~ valids = ("Serie", "Season", "Episode")
        #~ for i in range(len(selected)): 
            #~ cc = selected[:i+1]
            #~ if self.gettyp(cc) in valids: it.append(self.getname(cc))
        #~ return it
    
    # iterate from toplevel to current. (Pythonic as fuck)
    def getseriespath(self):
        c = self.treeview.get_cursor()[0]
        return [self.getname(c[:i+1]) for i in range(len(c)) if self.gettyp(c[:i+1]) in ("Serie", "Season", "Episode")]
    
    def mainwindow(self, size=(800,600), playerCmd="mplayer -fs '%s'"):
        """
        stand-alone (create window and bind eventhandlers)
        """
        self.playerCmd = playerCmd
        columns = ("Name", "", "", "AC", "Typ", "", "", None, None)
        cTypes  = (str, str, str, str, str, str, str, object, object)
        # you may wonder why there are this many columns in the tree store.
        # The AC (Number of Audiochannels) and the empty columns are not needed
        # (or used) but keeping them in places makes it very easy to use this
        # class as a plugin for Pselect as well as a standalone-GUI.
        
        # Movie list
        self.treestore = gtk.TreeStore(*cTypes) 
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.treestore)
        # create the TreeViewColumn to display the data
        cell = gtk.CellRendererText()                   # create a CellRenderer
        for cn in (0,4):
            one = gtk.TreeViewColumn(columns[cn])       # create column-object
            one.pack_start(cell, cn==0)                 # add cell & allow expansion, if first
            one.add_attribute(cell, 'text', cn)         # retrieve text from corresponding column in treestore
            self.treeview.append_column(one)            # add column to TreeView
            
        self.treeview.set_search_column(0)              # make it searchable
        
        # Create a ScrolledWindow with treeview and add it to a HBox
        self.scrollml = gtk.ScrolledWindow()
        self.scrollml.add(self.treeview)
        self.infoframe = gtk.Frame()
        self.infoframe.add(self.scrolledwindow2)
        self.hbox = gtk.HPaned()
        self.hbox.add1(self.scrollml)
        self.hbox.add2(self.infoframe)
        self.hbox.set_position(size[0]/2)
        
        # Main Window
        self.wind = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.wind.set_title("bs.to")
        if type(size) == str and size.lower() == "fullscreen":
            self.wind.maximize();
        elif type(size) in (tuple, list):
            self.wind.set_default_size(*size)
        self.wind.add(self.hbox)
        self.wind.show_all()
        
        # assign event-handlers
        self.wind.connect("destroy", gtk.main_quit) # or on ESC
        self.treeview.connect("key-press-event", self.on_keypressed)
        self.treeview.connect("cursor-changed",  self.on_cursor)
        self.treeview.connect("row-activated",   self.on_activate)
        
        self.populatefavorites()
        self.treeview.set_cursor(0)
        while gtk.events_pending(): gtk.main_iteration()
        return self.populatebsto()
    
    def msgBox(self, msg=""):
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK_CANCEL,
            None)
        dialog.set_markup(msg)
        dialog.set_default_response(gtk.RESPONSE_OK)
        resp = dialog.run()
        dialog.destroy()
        return resp == gtk.RESPONSE_OK
    
    def on_keypressed(self, win, evt):
        """
        Bind keyboard-shortcuts (only when stand alone aka self.mainwindow():
        """
        if evt.keyval == gtk.keysyms.F10:
            self.on_activate(self.treeview, special=True)
        
        if evt.keyval == gtk.keysyms.Escape: # ESC : Exit
            gtk.main_quit()
    
    def toggle_favorite(self):
        """
        if cursor is on a (existing) series it will be added to
        favorites or removed, if it's already a favorite.
        """
        cs = self.treestore.get_value(self.treestore.get_iter(self.treeview.get_cursor()[0]),0)
        if cs in self.favorites: # remove!
            if self.msgBox("<b>Remove</b>\n\n<i>"+cs+"</i>\n\nfrom favorites."):
                self.favorites.remove(cs)
                # iterate through favorite-childs. this feels a bit odd, there is
                # probably a better way to remove a treeviewitem "by name"
                for i in range(self.treestore.iter_n_children(self.faviter)):
                    ci = self.treestore.iter_nth_child(self.faviter, i)
                    if self.treestore.get_value(ci, 0) == cs:
                        self.treestore.remove(ci)
                        break
                self.savestate()
        elif cs in self.series.serDict.keys(): # add!
            if self.msgBox("<b>Add</b>\n\n<i>"+cs+"</i>\n\nto favorites."):
                self.favorites.append(cs)
                self.treestore.append(self.faviter, self.xc(cs, "Serie"))
                self.savestate()
        else:
            self.msgBox("<b>Error:</b> <i>"+cs+"</i> is invalid")
        self.treeview.grab_focus()
    
    def special(self, serpath):
        """
        Special action:
        Select mirror to
         - play
         - download to tmp & play on demand
         - download to dir
        """
        self.waitlabel("Getting mirrorlist...")
        mirs = self.series.getMirrors([unicode(x) for x in serpath])
        if mirs is None: return None
        title = " - ".join(serpath)
        dlgbox = widgets.MirrorDialog(title)
        
        for m in mirs: dlgbox.addOption(m)
        
        def play(txt):
            lnk = self.series.getStream([unicode(x) for x in serpath], self.waitlabel, txt)
            self.waitlabel("Spiele Stream\n...")
            self.playback(lnk)

        def temp(txt):
            lnk = self.series.getStream([unicode(x) for x in serpath], self.waitlabel, txt)
            self.waitlabel("download \n"+lnk+"\n to tmp")
            widgets.Download(lnk, "/tmp/tempvideofile", self.playback, True, title)

        def save(txt, fina):
            lnk = self.series.getStream([unicode(x) for x in serpath], self.waitlabel, txt)
            ext = ""
            if "." in lnk: ext = lnk.rsplit(".",1)[1]
            if len(ext) > 4 or ext == "" : ext=".mp4" # this is kind of a bad thing
            fina = fina+"."+ext
            self.waitlabel("download \n"+lnk+"\n to \n"+fina)
            widgets.Download(lnk, fina, self.playback, False, title)
        
        dlgbox.dispatch = {"play": play, "temp": temp, "save": save}
        dlgbox.launch()
        self.descrlabel(self.getseriespath()[0])
        return True
    
    def on_activate(self, tv, selected=None, cColumn=None, special=False):
        """
        Eventhandler for activating an entry. (Hitting "Enter")
        """
        selected = self.treeview.get_cursor()[0]
        citer = self.treestore.get_iter(selected)
        typ = self.gettyp()
        it = self.getseriespath()
        if "wind" in dir(self) and not special: # only if standalone
            if self.treestore.iter_has_child(citer):
                if not tv.row_expanded(selected):
                    tv.expand_row(selected, False)
                else:
                    tv.collapse_row(selected)
                return False
        
        if typ == "Serie":
            if special:
                self.toggle_favorite()
            elif not self.treestore.iter_has_child(citer):
                # if already watched, jump to the last viewed episode
                lsea = None
                if it[0] in self.lastbyseries.keys():
                    lsea = self.lastbyseries[it[0]][0]
                # expand Seasons
                self.waitlabel("Lade Staffelliste...")
                cc = 0
                selected_sub = None
                for s in self.series.getSeasons(unicode(it[0])):
                    if s == lsea: selected_sub = selected + (cc,)
                    cc += 1
                    piter = self.treestore.append(citer, self.xc(s, "Season"))
                self.treeview.expand_row(selected, False)
                if selected_sub:
                    self.treeview.set_cursor(selected_sub)
                    self.on_activate(tv)
        
        if typ == "Season" and not self.treestore.iter_has_child(citer):
            # expand Episodes
            self.waitlabel("Lade Episodenliste...")
            lepi = None
            if it[0] in self.lastbyseries.keys():
                lepi = self.lastbyseries[it[0]][1]
            cc = 0
            selected_sub = None
            for s in self.series.getEpisodes(unicode(it[0]), unicode(it[1])):
                if s == lepi: selected_sub = selected + (cc,)
                cc += 1
                piter = self.treestore.append(citer, self.xc(s, "Episode"))
            self.treeview.expand_row(selected, False)
            if selected_sub:
                self.treeview.set_cursor(selected_sub)
        
        if typ == "Episode":
            did = False
            if special:
                did = self.special(it)
            else:
                self.waitlabel("Suche Streamlink\n...")
                lnk = self.series.getStream([unicode(x) for x in it], self.waitlabel)
                if lnk:
                    self.waitlabel("Spiele Stream\n...")
                    self.playback(lnk)
                    did = True
            if did:
                self.lastviewed = it
                self.lastbyseries[it[0]] = (it[1], it[2])
                self.savestate()
        
        if len(it) > 0 and "Description" in self.series.serDict[unicode(it[0])]:
            self.descrlabel(it[0])
        else: 
            self.resetlabel()
        self.treeview.grab_focus()
    
    def playback(self, url):
        """
        Playback URL. May be overwritten, when used as a plugin.
        """
        os.system(self.playerCmd % url)
    
    def on_cursor(self, tv=None):
        # is our info-widget currently displayed in infoframe?
        # this is only useful when used as a plugin.
        if self.infoframe.get_child() != self.scrolledwindow2:
            self.infoframe.remove(self.infoframe.get_child())
            self.infoframe.add(self.scrolledwindow2)
        it = self.getseriespath()
        if self.series and len(it) > 0 and "Description" in self.series.serDict[unicode(it[0])]:
            self.descrlabel(it[0])
        else: 
            self.resetlabel()
    
    def populatefavorites(self, ev=None, node=None):
        """
        This populates the main tree (adding favorites). Call this, after treeview & treestore are overwritten.
        """
        # Add Favorites instantly
        self.faviter = self.treestore.append(node, self.xc(u"✪ Favoriten", "Genre"))
        for ser in self.favorites:
            self.treestore.append(self.faviter, self.xc(ser, "Serie"))
    
    def populatebsto(self, node=None):
        """
        Load streamsites and populates the tree further. Call this after the favorites are populated.
        """
        if self.series:
            return True
        self.waitlabel("Lade Serienliste\n...")
        # fill with series-list
        try:
            # self.series = streamsite.Serienstream()
            # self.series = streamsite.Burningseries()
            self.series = streamsite.Metastream()
        except RuntimeError as e:
            self.waitlabel(e.args[0])
            return False
        alliter = self.treestore.append(node, self.xc(u"Alphabetisch", "Genre"))
        osl="" # old start letter. we're going to group "All" by letter.
        for ser in self.series.getSeries():
            nsl = ser[0].upper()
            if nsl in "123456789":
                nsl = "0"
            if nsl != osl:
                subiter = self.treestore.append(alliter, self.xc(nsl, "Genre"))
                osl = nsl
            self.treestore.append(subiter, self.xc(ser, "Serie"))
        # add genres
        
        alliter = self.treestore.append(node, self.xc(u"Genres", "Genre"))
        for gen in self.series.getGenres():
            geniter = self.treestore.append(alliter, self.xc(gen, "Genre"))
            for ser in self.series.getSeries(gen):
                self.treestore.append(geniter, self.xc(ser, "Serie"))
        self.resetlabel()
        return True
    
    def resetlabel(self):
        lv = self.lastviewed
        self.description.set_justify(gtk.JUSTIFY_CENTER)
        self.description.set_alignment(0.5, 0.2)
        self.description.set_line_wrap(True)
        self.description.set_label(
            "<span color='"+bspconfig.logobordercolor+"' font='monospace' size='"+str(bspconfig.logosize)+"'>"+
            " ╭───────────────╮ \n"+
            " │ <span color='"+bspconfig.logocolor+"'>Serien Online</span> │ \n"+
            " ╰───────────────╯ \n</span>"+
            "<span color='"+bspconfig.logocolor+"' size='"+str(bspconfig.logosize)+"'>"+str(self.series)+"</span>\n\n"+
            "<span underline='single' color='"+bspconfig.headingcolor+"'>Zuletzt gesehen:</span>\n\n"+
            "<b>"+lv[0].replace("&", "&amp;")+"</b>"+"<span font='8'>\n\n</span>"+
            lv[1].replace("&", "&amp;")+"<span font='8'>\n\n</span>"+
            "<i>"+lv[2].replace("&", "&amp;")+"</i>"+
            "\n\n\n\n"+
            "<span color='"+bspconfig.helpcolor+"' size='"+str(bspconfig.helpsize)+"'>"+
            "[F10] Mirrorauswahl &amp; Download\noder Favorit hinzufügen/löschen.</span>")
    
    def waitlabel(self, message):
        self.description.set_justify(gtk.JUSTIFY_CENTER)
        self.description.set_alignment(0.5, 0.5)
        self.description.set_line_wrap(False)
        self.description.set_label(
            "<span font='"+str(bspconfig.waiticonsize)+"' color='"+bspconfig.waiticoncolor+"'>"+
            bspconfig.waiticon+"</span>\n\n"+
            "<span color='"+bspconfig.waittextcolor+"'>"+message+"</span>"
        )
        while gtk.events_pending(): gtk.main_iteration()
    
    def descrlabel(self, seri):
        self.description.set_justify(gtk.JUSTIFY_LEFT)
        self.description.set_alignment(0.5, 0)
        self.description.set_line_wrap(True)
        lastview = ""
        if seri in self.lastbyseries.keys():
            lastview += "<u>Zuletzt gesehen:</u>\n\n<i>"
            lastview += " - ".join(x.replace("&", "&amp;") for x in self.lastbyseries[seri])
            lastview += "</i>\n\n"
        self.description.set_label(
            "<span color='"+bspconfig.headingcolor+"'><b>"+seri.replace("&", "&amp;")+"</b>\n"+
            "\n"+lastview+"</span>"+
            "<span color='"+bspconfig.textcolor+"'>"+self.series.serDict[unicode(seri)]["Description"]+"</span>"
        )
    


    # Alternativ zu diesem ASCII-Datei ex- und import ginge auch 
    # pickle([self.lastviewed, self.lastbyseries, self.favorites])
    # Ich mags so, wegen der Menschenlesbarkeit.
    def loadstate(self):
        # try reading from textfile (only done once at startup):
        # first line in FavFile is the last viewed item
        # every line starting with SPLORT contains the last viewed item for a specific series
        # all other lines are the favorites
        if not os.path.exists(self.FavFile): return None
        ff = open(self.FavFile, "r")
        self.lastviewed = ff.readline().strip().split(SPLORT) # unicode(readline)??
        if len(self.lastviewed) < 3: self.lastviewed = ["", "", ""]
        for l in ff:
            l = l.strip("\n")
            if l.startswith(SPLORT):
                l = l.split(SPLORT)
                self.lastbyseries[l[1]] = (l[2], l[3])
            else: # if l in self.series.serDict.keys():
                self.favorites.append(l)
        ff.close()
        
    
    def savestate(self):
        ff = open(self.FavFile, "w")
        # write last viewed item
        ff.write(SPLORT.join(self.lastviewed) + "\n")
        # write all last viewed by series
        for k, v in self.lastbyseries.items():
            ff.write(SPLORT + k + SPLORT + SPLORT.join(v) + "\n")
        # write favorites
        for l in self.favorites: ff.write("%s\n" % l)
        ff.close()

