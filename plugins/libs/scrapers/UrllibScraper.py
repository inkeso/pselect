#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import urllib2, re
from bs4 import BeautifulSoup
from ..scrapers import preprocess

class Scraper():
    def supper(self, url):
        heads = {'User-agent':'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        req = urllib2.Request(url, headers=heads)
        response = urllib2.urlopen(req)
        nurl = response.geturl()
        content = response.read()
        response.close()
        return BeautifulSoup(preprocess(content), "html.parser")
