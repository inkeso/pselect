#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import gtk, gobject, webkit, threading
from bs4 import BeautifulSoup

class Scraper():
    def __init__(self):
        gobject.threads_init()
        self.broz = webkit.WebView()
        self.broz.connect("load-finished", self.get_source)

    def get_source(self, web, frame):
        data = frame.get_data_source().get_data()
        if data is not None:
            html = frame.get_data_source().get_data()
            if not "banhammer" in html and len(html) > 5000: 
                self._html = html
                self._uri = frame.get_uri()
                self._wait = False

    def beautifulthread(self, html):
        self._html = BeautifulSoup(preprocess(html), "html.parser")
        # emit a gtk-event when finished (and unset wait-flag for wrapper self.supper)
        self.broz.emit("realize")
        self._wait = False

    def supper(self, url, raw=False):
        # 1. Step: get response
        self._wait = True
        self.broz.open(url)
        while self._wait or gtk.events_pending(): gtk.main_iteration()
        # 2. Step: Parse it
        self._wait = True
        thread = threading.Thread(target=self.beautifulthread, args=(html,))
        gobject.idle_add(thread.start)
        while self._wait or gtk.events_pending(): gtk.main_iteration()
        return self._html
