#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os, re
if 'DISPLAY' in os.environ and os.environ['DISPLAY']:
    import gtk, webkit
else:
    raise Exception("WebkitScraper needs a running X-Server")

from ..bs4 import BeautifulSoup
from ..scrapers import preprocess

class Scraper():
    def __init__(self):
        self.broz = webkit.WebView()
        self.broz.connect("load-finished", self.get_source)

    def get_source(self, web, frame):
        while gtk.events_pending(): gtk.main_iteration()
        data = frame.get_data_source().get_data()
        if data is not None:
            if not "banhammer" in data and len(data) > 5000:
                self._html = BeautifulSoup(preprocess(data))
                self._wait = False

    def supper(self, url):
        self._wait = True
        self.broz.open(url)
        while self._wait or gtk.events_pending(): gtk.main_iteration()
        return self._html

