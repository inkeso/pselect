#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#   kinoxparser.py
#   
#   Copyright 2015 Eloi Maelzer
#   
#   This parses kinox.to, grabs video-links, decodes them to 
#   a directly streamable link.


#   ID    : Hoster                       #  Geht?
#   ------:------------------------------#--------------
ValidHosters = { 
    "7"   :  "WholeCloud.net"           ,#  Nope
    "8"   :  "CloudTime.to"             ,#  ytdl
    "15"  :  "AuroraVid.to"             ,#  ytdl
    "24"  :  "VideoWeed.es → bitvid.sx" ,#  ytdl
    "30"  :  "StreamCloud.eu"           ,#  OK
    "31"  :  "XvidStage.com"            ,#  Nope
    "33"  :  "FlashX.tv"                ,#  Nope
    "36"  :  "HostingBulk.com"          ,#  Off
    "40"  :  "NowVideo.sx"              ,#  ytdl
    "45"  :  "PrimeShare.tv"            ,#  OK
    "49"  :  "MooShare.biz"             ,#  Off
    "50"  :  "VidBull.com"              ,#  Nope
    "51"  :  "VidTo.me"                 ,#  ytdl
    "52"  :  "Shared.sx"                ,#  OK
    "56"  :  "Promptfile.com"           ,#  OK
    "57"  :  "Mightyupload"             ,#  Nope
    "58"  :  "TheVideo.me"              ,#  OK
    "60"  :  "CloudZilla.To"            ,#  Nope
    "61"  :  "ShareSix.com"             ,#  ytdl
    "62"  :  "LetWatch.us"              ,#  Nope
    "63"  :  "RealVid.net"              ,#  Nope
    "65"  :  "VodLocker.com"            ,#  OK
    "67"  :  "OpenLoad.co"              ,#  ytdl
    "68"  :  "Vidzi.tv"                 ,#  ytdl
} # See also: streamhoster.py

# Try these Hosters in this order
HosterRank = ("30", "56", "45", "58", "52", "65",     # simple
              "7", "8", "15", "24", "40", "61", "67", "68") # youtube-dl [TODO]

import urllib

from ..libs.bs4 import BeautifulSoup
from ..libs import streamhoster


class ValidBrowser(urllib.FancyURLopener):  # I'm a Firefox. Really.
    version = "Mozilla/5.0 (X11; Linux x86_64; rv:25.8) Gecko/20151126 Firefox/31.9"

class Kinox():
    Languages = {
        "1" : "(de)", "2" : "(en)", "15": "(de/en)"
    }
    # außerdem verfügbar:
    # "4" : "Chinesisch",   "5" : "Spanisch",        "6" : "Französisch",
    # "7" : "Türkisch",     "8" : "Japanisch",       "9" : "Arabisch",
    # "11": "Italienisch",  "16": "Niederländisch",  "12": "Kroatisch",
    # "13": "Serbisch",     "14": "Bosnisch",        "17": "Koreanisch",
    # "24": "Griechisch",   "25": "Russisch",        "26": "Indisch"
    
    def __init__(self):
        self.URL = "http://www.kinox.to/"
        self.broz = ValidBrowser()
    
    def supper(self, url):
        http = self.broz.open(self.URL + url)
        page = http.read()
        http.close()
        return(BeautifulSoup(page))
    
    def search(self, word):
        """
        Search kinox.to, return a list:
        [(Language, Title, Vid-ID), (...)]
        if word is "Popular" or "Latest", we grab the corresponding list
        instead of searching
        """
        result = []
        if word in ("Popular", "Latest"):
            soup = self.supper(word+"-Movies.html")
        else:
            soup = self.supper("Search.html?q=" + urllib.quote_plus(word))
        tab = soup.find(id="RsltTableStatic")
        for ro in tab.findAll("tr"):
            link = ro.find("a")
            if not link: continue
            vidid = link.get("href").replace("/Stream/","").replace(".html", "")
            title = link.text
            lang = ro.find("img", alt="language").get("src").strip("/grsylnp.")
            if lang in self.Languages:
                result.append((self.Languages[lang], title, vidid))
        return result
    
    def getMirros(self, vidid):
        """
        Return a list of available Hoster_IDs
        """
        soup = self.supper("Stream/"+vidid+".html")
        hosts = []
        for x in soup.find("ul", id="HosterList").findAll("li"):
            hosts.append(x.get("id").split("_")[1])
        return hosts

    def getInfo(self, vidid):
        """
        Return movie-info as HTML-snippet.
        I probably should find a better solution for all those try..catch-blocks
        (OnErrorResumeNext? ;P)
        """
        soup = self.supper("Stream/"+vidid+".html")
        desc = BeautifulSoup()
        try:    desc.append(soup.find("div", "ModuleHead").find("h1"))
        except: pass
        try:    desc.append(soup.find("div", "Grahpics")) # yes. Grahpics.
        except: pass
        try:    dt = soup.find("ul", id="DetailTree")
        except: pass
        try:    desc.append(dt.find("li", title="Genre"))
        except: pass
        try:    desc.append(dt.find("li", title="Runtime"))
        except: pass
        try:    desc.append(soup.find("div", "Descriptore"))
        except: pass
        try:    desc.append(dt.find("li", title="Director"))
        except: pass
        for h in HosterRank:
            try:    desc.append(soup.find("li", id="Hoster_"+h).find("div", "Named"))
            except: pass
        
        return str(desc)
    
    def getStream(self, vidid, output, hst=HosterRank):
        """
        get best available stream. (priority: see self.Hosters)
        vidid is the video-id from kinox (see self.search())
        output is a function, accepting a string as first and only parameter
        hst is the list of hoster-IDs to be checked in this order
        """
        assert type(hst) in (list, tuple)
        for h in hst:
            output("Loading "+vidid+" from "+ValidHosters[h])
            soup = self.supper("aGET/Mirror/"+vidid+"&Hoster="+h)
            lnk = soup.find("a")
            if lnk:
                durl = lnk.get("href").replace("\\","").replace("\"","")
                durl = durl.replace("/Out/?s=", "")
                print durl
                output("Load "+ durl)
                parsed = streamhoster.findParser(durl, output)
                if parsed: return parsed
        output("No suitable mirror found")
        return None


