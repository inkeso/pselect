#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  widgets.py
#  
#  Copyright 2016 Eloi Maelzer <iks@SteroiX>
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
#  
#  

import urllib2, gtk, gobject, os
import threading, time

gobject.threads_init()

def byte2hr(size):
    '''
    Return a string representing a human readable representation of a
    filesize
    '''
    _abbrevs = [(1<<50L,'PiB'), (1<<40L,'TiB'), (1<<30L,'GiB'), 
                (1<<20L,'MiB'), (1<<10L,'KiB'), (1, 'B')]
    for factor, suffix in _abbrevs:
        if size >= factor:
            break
    if suffix == 'B': return '%d %s' % (size/float(factor), suffix)
    return '%0.2f %s' % (size/float(factor), suffix)


class Download():
    def __init__(self, source, target, playcmd=None, removedefault=False, title=""):
        
        self._startime = 0 # set in downloadthread
        self._stop = False
        self.source = source
        self.target = target
        
        self.dlg = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.dlg.set_title("Download: "+title)
        self.dlg.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        hrtarg = target
        hrsrc = source
        if len(source) > 80: 
            hrsrc = source[:56] + " ... " + source[-19:]
        self.label=gtk.Label("%s  \n --   ↓ ↓ ↓   --\n%s  " % (hrsrc, target))
        self.progress=gtk.ProgressBar()
        self.delete = gtk.CheckButton("Delete afterwards")
        self.delete.set_active(removedefault)
        
        self.playbutt = gtk.Button(stock=gtk.STOCK_MEDIA_PLAY)
        self.playbutt.connect("clicked", lambda x: playcmd(target))
        self.cancbutt = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.cancbutt.connect("clicked", lambda x: self.dlg.destroy())
        self.buttbox = gtk.HBox()
        self.buttbox.pack_start(self.playbutt, True, True, 10)
        self.buttbox.pack_start(self.cancbutt, True, True, 10)

        self.vbox = gtk.VBox()
        self.dlg.add(self.vbox)
        self.vbox.pack_start(self.label, True, True, 10)
        self.vbox.pack_start(self.progress, True, True, 10)
        self.vbox.pack_start(self.delete, True, True, 10)
        self.vbox.pack_start(self.buttbox, True, True, 10)
        
        self.dlg.show_all()
        self.dlg.connect("destroy", self.destroy)
        
        # start download-thread
        self.dlthread = threading.Thread(target=self.downloadthread, args=())
        gobject.idle_add(self.dlthread.start)
    
    def destroy(self, wtf=None):
        self._stop = True # this should end the download-thread
        self.dlthread.join()
        # delete?
        if self.delete.get_active():
            os.unlink(self.target)
        self.dlg.destroy()
    
    def downloadthread(self, blocksize=32*1024):
        # download in a thread, progress is a gtk.ProgressBar widget to display the progress
        self._starttime = time.time()
        try:
            u = urllib2.urlopen(self.source)
        except:
            self.progress.set_text("404: File not found")
            # keep this thread runing
            self.cancbutt.set_label(gtk.STOCK_CLOSE)
            self.cancbutt.set_use_stock(True)
            while not self._stop: time.sleep(.05)
            return
        f = open(self.target, 'wb')
        size = int(u.info().getheaders("Content-Length")[0])
        dl = 0
        while not self._stop:
            buff = u.read(blocksize)
            if not buff: break # done
            dl += len(buff)
            f.write(buff)
            if size > 0: 
                frac = float(dl) / size
                delta = time.time() - self._starttime
                etas = time.strftime("%H:%M:%S", time.gmtime(delta / frac - delta))
                self.progress.set_fraction(frac)
            else:
                etas = "Uknown"
                self.progress.pulse()
            gtk.gdk.threads_enter()
            self.progress.set_text("%s / %s    [ETA: %s]" % (byte2hr(dl), byte2hr(size), etas))
            
            gtk.gdk.threads_leave()
        f.close()
        self.progress.set_fraction(1)
        self.progress.set_text("DONE")
        self.cancbutt.set_label(gtk.STOCK_CLOSE)
        self.cancbutt.set_use_stock(True)
        # keep thread running
        while not self._stop: time.sleep(.05)


class MirrorDialog:
    def __init__(self, title):
        self.title = title
        self.mirrorframe = gtk.Frame("Mirror")
        self.mirrorframe.set_label_align(.5, .5)
        self.mirrorframe.set_border_width(5)
        self.mirrortab = gtk.VBox(spacing=5)
        self.mirrortab.set_border_width(5)
        self.mirrorframe.add(self.mirrortab)
        
        self.murl = gtk.Label("-")
        self.murl.set_padding(5, 10)
        
        self.playBtn = gtk.Button(stock=gtk.STOCK_MEDIA_PLAY)
        self.tempBtn = gtk.Button("Download to /tmp")
        self.saveBtn = gtk.Button(stock=gtk.STOCK_SAVE_AS)
        self.closBtn = gtk.Button(stock=gtk.STOCK_CANCEL)
        for b in (self.playBtn, self.tempBtn, self.saveBtn, self.closBtn):
            b.connect("clicked", self.action)
        
        self.selectedvbox = gtk.VBox(spacing=5)
        self.selectedvbox.pack_start(self.murl)
        self.selectedvbox.pack_start(self.playBtn)
        self.selectedvbox.pack_start(self.tempBtn)
        self.selectedvbox.pack_start(self.saveBtn)
        self.selectedvbox.pack_start(self.closBtn)

        self.selectedframe = gtk.Frame("Action")
        self.selectedframe.set_label_align(.5, .5)
        self.selectedframe.set_border_width(5)
        self.selectedframe.add(self.selectedvbox)

        self.dlghbox = gtk.HBox(homogeneous=True, spacing=5)
        self.dlghbox.pack_start(self.mirrorframe)
        self.dlghbox.pack_start(self.selectedframe)
        
        self.miBtns = []
        self.dispatch = { # overwrite these with your custom function
            "play": None, # def play(txt)
            "temp": None, # def temp(txt)
            "save": None  # dev save(txt, fina)
        }

    def mkLabs(self, obj, fdir=None):
        if obj.get_active() or fdir:
            self.murl.set_text(obj.get_label())
            for b in self.miBtns: b.set_active(b == obj)
        if all(not b.get_active() for b in self.miBtns):
            obj.set_active(True)
    
    def addOption(self, txt):
        cb = gtk.ToggleButton(txt)
        cb.connect("focus", self.mkLabs)
        cb.connect("clicked", self.mkLabs)
        self.miBtns.append(cb)
        self.mirrortab.pack_start(cb)
    
    def launch(self):
        self.dlghbox.show_all()
        self.dlg = gtk.Dialog("Special Action: "+self.title, None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        self.dlg.vbox.pack_end(self.dlghbox, True, True, 0)
        self.dlg.run()
    
    def action(self, obj):
        murlstr = self.murl.get_text()
        self.dlg.destroy()
        if obj == self.closBtn: return
        if obj == self.playBtn: self.dispatch["play"](murlstr)
        if obj == self.tempBtn: self.dispatch["temp"](murlstr)
        if obj == self.saveBtn:
            pth = gtk.FileChooserDialog("Save as...", None, 
                        gtk.FILE_CHOOSER_ACTION_SAVE, 
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_SAVE,gtk.RESPONSE_OK)
            )
            pth.set_current_name(self.title)
            saved = pth.run()
            fina = pth.get_filename()
            pth.destroy()
            if saved == gtk.RESPONSE_OK: self.dispatch["save"](murlstr, fina)


