#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
Yes, they are quite small and i would love to keep them in one file but since
the need different imports i have to have a separate file for each of them.
(i don't want to import e.g. webkit if using urllib2-scraper)
'''

import re, urllib2

def preprocess(rawhtml):
    '''BeautifulSoup sometime chokes on comments and terribly placed inline-scripts.'''
    rawhtml = re.sub("<script.+?/script>", "", rawhtml, flags=re.DOTALL)
    rawhtml = re.sub("<!.+?-->", "", rawhtml, flags=re.DOTALL)
    return rawhtml

def redirected(url):
    '''
    Simple urllib-based request to find redirected URL. webkit does provide
    webkit.WebView().get_main_frame().get_uri() but it doesn't work as intended.
    This works for bioth bs.to & sereienstream.to outgoing redirections.
    '''
    heads = {'User-agent':'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
    req = urllib2.Request(url, headers=heads)
    response = urllib2.urlopen(req)
    nurl = response.geturl()
    response.close()
    return nurl

