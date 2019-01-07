#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import urllib

from bs4 import BeautifulSoup

VIDEOTEMPLATE = """
<html><head><body>
  <h1>{h1}</h1><h2>{h2}</h2>
  <h3>{speaker}, {date}, {duration}</h3>
  <div>{about}</div>
</body></html>
"""

def supper(url):
    http = urllib.urlopen(url)
    page = http.read()
    http.close()
    return BeautifulSoup(page, "html.parser")

def getItem(root="/b/"):
    idx = supper("https://media.ccc.de"+root)
    folders = []
    items = []
    video = []
    
    for fldr in idx.find_all("a", "thumbnail"):
        cap = fldr.find_all("div", "caption")
        if len(cap) == 0: continue
        lnk = fldr.get("href")
        folders.append([cap[0].string.strip(), lnk])
    
    for item in idx.find_all("div", "event-preview"):
        cap = item.h3.a.string.strip()
        lnk = item.a.get("href")
        dur, dat, usr = ("", "", "")
        for li in item.ul.find_all("li"):
            if not li.span: continue
            if "icon-clock-o" in li.span.get("class"):
                try:
                    dur = "%02d:%02d:00" % divmod(int(li.text.strip().replace(" min","")), 60)
                except ValueError:
                    pass
            if "icon-calendar-o" in li.span.get("class"): 
                dat = ".".join(reversed(li.text.strip().split("-")))
            if "persons" in li.span.get("class"):
                usr = li.text.strip()
        items.append([cap, lnk, dur, dat, usr])
    
    if (idx.video):
        # H1, H2, About, Duration, Date, Speaker(s), {VideoURLs}
        p = idx.find("p", "persons")
        d = idx.find("p", "description")
        t = idx.find("span", "icon icon-clock-o")
        c = idx.find("span", "icon icon-calendar-o")
        meta = {
            "h1": idx.h1.string.strip() if idx.h1 else "",
            "h2": idx.h2.string.strip() if idx.h2 else "",
            # TODO: better fixing for ugly glitch
            "speaker": p.getText()[:p.getText().find("\n\n\n\n\n\n")].strip() if p else "",
            "about": d.text.strip() if d else "",
            "date": ".".join(reversed(c.parent.text.strip().split("-"))) if c else "",
            "duration": t.parent.text.strip() if t else ""
        }
                                 # use the first available videosrc.
        metahtml = VIDEOTEMPLATE.format(**meta)
        # get all available video-sources (different languages & formats)
        sources = {}
        for src in idx.video.find_all("source"):
            sources[src.get("title")] = src.get("src")
        video = [meta, metahtml, sources]
    
    ilen = [len(x) for x in (folders, items, video)]
    if sum(ilen) != max(ilen):
        print "WARN: Ambiguous page. Found %d folders, %d items, %d videos" % ilen
    
    if ilen[0] > 0: return("FOLDERS", sorted(folders, key=lambda x: x[0]))
    if ilen[1] > 0: return("VIDEOLIST", sorted(items, key=lambda x: x[0]))
    if ilen[2] > 0: return("VIDEO", video)
