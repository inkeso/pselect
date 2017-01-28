#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#   streamsite.py
#
#   This class parses bs.to and serienstream.to for a list of series and their streamlinks.

from sys import stderr
import re, time

from ..libs.odict import OrderedDict as OD
from ..libs import streamhoster

# urllib is faster but sometimes e "real" browser is needed
from ..libs.scrapers.WebkitScraper import Scraper as WebkitScraper
from ..libs.scrapers.UrllibScraper import Scraper as UrllibScraper
from ..libs.scrapers import redirected

# Metastream uses threading... Webkit uses GTK. We must use gobject-threading.
from threading import Thread
import gobject, gtk
gobject.threads_init()


class Streamsite:
    # which Hosters do we prefer?
    Hosters = ["streamcloud.eu", "powerwatch.pw"]
    # add others (simple ones)
    Hosters.extend(set(streamhoster.listHosters("simple")) - set(Hosters))
    # add others (with youtube-dl)
    Hosters.extend(set(streamhoster.listHosters("youtube-dl")) - set(Hosters))
    
    def __init__(self, url="", scraper=WebkitScraper):
        self.URL = url
        self.scraper = scraper()
        # get genres in a ordered dict. Each Value contains an ordered
        # dict of all the series of this genre.
        self.genDict = OD()
        # also, there is a dict with all series regardless of the genre
        self.serDict = OD()
        for genre in self._genreSoup():
            genrestr = self._genreTitle(genre)
            self.genDict[genrestr] = OD()
            for a in genre.find_all("a"):
                surl = OD([("URL", a.get("href").replace(self.URL, ""))])
                tit = None
                if a.string: tit = a.string
                else: tit = a.get("title").replace(" Stream anschauen","")
                if tit:
                    self.genDict[genrestr][tit] = surl
                    self.serDict[tit] = surl
        if len(self.serDict) == 0:
            raise RuntimeError("Loading %s failed" % self.URL.split("/")[2])
    
    def supper(self, url):
        return(self.scraper.supper(self.URL + url))
    
    def __repr__(self):
        return "%d Serien in %d Genres (%s)" % (len(self.serDict), len(self.genDict), self.URL)
    
    def getGenres(self):
        return self.genDict.keys()
    
    def getSeries(self, genre=None):
        """
        return a list of series, belonging to a genre.
        If genre is None, all series are returned
        """
        ks = self.serDict.keys() if genre is None else self.genDict[genre].keys()
        ks.sort(key=lambda x: x.lower())
        return ks
    
    def getSeasons(self, serie):
        """
        Add a description and a list of seasons to the dict of a given series
        (if it isn't there already):
        self.serDict[serie] = OD {
            "URL": "http://example.com/link/to/series",
            "Description": "Once upon a time",
            "Season 1": {
                "URL": "http://example.com/link/to/season-1"
                "Episodes": OD {} # will be filled by getEpisodes(),
            }
            "Season 2": {}, ...
        }
        also return a list of seasons (strings)
        """
        if serie not in self.serDict.keys(): return None
        if "Description" not in self.serDict[serie].keys():
            url = self.serDict[serie]["URL"]
            soup = self.supper(url)
            self.serDict[serie]["Description"] = self._seasonDescription(soup)
            for s in self._seasonList(soup):
                self.serDict[serie][self._seasonTitle(s)] = OD([("URL", s.get("href").replace(self.URL, ""))])
        return [x for x in self.serDict[serie].keys() if x.startswith("Season")]
    
    def getDescription(self, serie):
        if serie in self.serDict and "Description" in self.serDict[serie]:
            return self.serDict[serie]["Description"]
        else:
            return ""

    def getEpisodes(self, serie, season):
        """
        Add Episodes to self.serDict:
        self.serDict[serie][season]["Episodes"] = OD {
            "A New Episode": value,
        }
        value may be a url or list of urls to the episode-page on the streamsite
        depending on the implementation.
        also return a list of episodes (strings)
        """
        if serie not in self.serDict.keys(): return None
        if season not in self.serDict[serie].keys(): return None
        if "Episodes" in self.serDict[serie][season]: 
            return self.serDict[serie][season]["Episodes"].keys()
        seaUrl = self.serDict[serie][season]["URL"]
        slist = OD()
        for e in self._episodesList(self.supper(seaUrl)):
            slist[self._episodesTitle(e)] = self._episodesValue(e)
        self.serDict[serie][season]["Episodes"] = slist
        return slist.keys()
    
    # Any implementation should overwrite following methods (to use the defaults above):
    # see __init__:
    def _genreSoup(self, surl): pass
    def _genreTitle(self, genreitem): pass
    # see getSeasons:
    def _seasonTitle(self, soup): pass
    def _seasonDescription(self, soup): pass
    def _seasonList(self, soup): pass
    # see getEpisodes:
    def _episodesTitle(self, soup): pass
    def _episodesList(self, soup): pass
    def _episodesValue(self, soup): pass
    # instead __init__, getSeasons and getEpisodes may be overwriten entirely.
    
    def getMirrors(self, serpath):
        """
        serpath is a tuple ("series", "season", "episode")
        this function returns a OD {
            "streamhoster1": "link to streamhoster1",
            "streamhoster2": "link to streamhoster2",
        }
        The links may be indirect and further decoded in self.getStream(),
        depending on the implementation.
        """
        pass
    
    def getStream(self, serpath, output=stderr.write, mirror=None):
        """
        get stream-url for this episode. if mirror is a valid hoster (key in the
        OD from getMirrors) only this one is used.
        Otherwise all available (and valid) mirrors are tried.
        """
        pass

class Burningseries(Streamsite):
    def __init__(self):
        Streamsite.__init__(self, "https://www.bs.to/", scraper=UrllibScraper)
    
    def _genreSoup(self):
        return self.supper("serie-genre").find_all("div", "genre")
    
    def _genreTitle(self, genreitem):
        return genreitem.span.strong.string
    
    def _seasonDescription(self, soup):
        return soup.find("div", id="sp_left").div.p.string
    
    def _seasonList(self, soup):
        return soup.find("ul", "clearfix").findChildren("a")[:-1]
    
    def _seasonTitle(self, soup):
        return "Season "+soup.string
    
    def _episodesTitle(self, soup):
        title = soup.findChild("strong")
        if not title: title = soup.findChild("span")
        return soup.find("td").string+" "+title.string
    
    def _episodesList(self, soup):
        return soup.find("table").findAll("tr")[1:]
    
    def _episodesValue(self, soup):
        slnk = OD()
        hosts = list(self.Hosters) # make copy, keep original intact
        # openload will be removed here, because bs.to doesn't provide a direct
        # link and using the embedded one with youtube-dl doesn't work.
        if "openload.co" in hosts: hosts.remove("openload.co")
        for x in soup.findAll("a", "icon"):
            if re.search(x["title"].lower(), " ".join(hosts)):
                slnk[x["title"]] = x["href"]
        return slnk
    
    def getMirrors(self, serpath):
        serie, season, episode = serpath
        if serie not in self.serDict.keys(): return None
        if season not in self.serDict[serie].keys(): return None
        if episode not in self.serDict[serie][season]["Episodes"].keys(): return None
        return self.serDict[serie][season]["Episodes"][episode]
    
    def getStream(self, serpath, output=stderr.write, mirror=None):
        mirs = self.getMirrors(serpath)
        if mirs is None:
            output("No mirrors found for "+" - ".join(serpath))
            return None
        if mirror is not None and mirror not in mirs.keys(): return None
        if mirror in mirs.keys():
            tryhost = [mirror]
        else:
            tryhost = mirs.keys()
        
        for mir in tryhost:
            output("Loading %s from %s" % (" - ".join(serpath), mir))
            soup = self.supper(mirs[mir])
            links = [l.get("href") for l in soup.findAll("a", target="_blank") if l.text.find("Originalvideo") > -1]
            for link in links:
                output("fetching stream from %s" % link)
                # one redirect
                link = redirected(link)
                streamurl = streamhoster.findParser(link, output)
                if streamurl is not None: return streamurl
        output("No suitable stream found")
        return None

class Serienstream(Streamsite):
    def __init__(self):
        Streamsite.__init__(self, "http://serienstream.to", scraper=WebkitScraper)

    def _genreSoup(self):
        return self.supper("/serien").find_all("div", "genre")
    
    def _genreTitle(self, genreitem):
        return genreitem.div.h3.string
    
    def _seasonDescription(self, soup):
        return soup.find("p", "seri_des").get("data-full-description")
    
    def _seasonList(self, soup):
        return soup.find("div", "hosterSiteDirectNav").findChildren("ul")[0].findChildren("a")
    
    def _seasonTitle(self, soup):
        return soup.get("title").replace("Staffel", "Season")
    
    def _episodesTitle(self, soup):
        a = soup.findChildren("a")[1]
        title = a.findChild("strong").text
        if not title: title = a.findChild("span").text
        return soup["data-episode-season-id"]+" "+title
    
    def _episodesList(self, soup):
        return soup.find("table", "seasonEpisodesList").findChildren("tr")[1:]
    
    def _episodesValue(self, soup):
        return {"URL": soup.findChildren("a")[1]["href"]}
    
    def getMirrors(self, serpath):
        serie, season, episode = serpath
        try: epi = self.serDict[serie][season]["Episodes"][episode]
        except: return None
        if "Mirrors" in epi: return epi["Mirrors"]
        valid = re.compile("|".join(map(lambda x: x[:x.index(".")], self.Hosters)), flags=re.IGNORECASE)
        langcode = {"1": "DE", "2": "EN", "3": "EN+de"}
        slnk = OD()
        soup = self.supper(epi["URL"])
        mirrors = soup.find("div", "hosterSiteVideo").findChildren("li")
        for l in mirrors:
            if not valid.search(l.h4.text): continue # skip invalid hosters
            key = "%s - %s (%02d)" % (langcode[l["data-lang-key"]], l.h4.text, len(slnk)+1)
            slnk[key] = self.URL + l.a["href"]
        epi["Mirrors"] = slnk
        return slnk
    
    def getStream(self, serpath, output=stderr.write, mirror=None):
        mirs = self.getMirrors(serpath)
        if mirs is None:
            output("No mirrors found for "+" - ".join(serpath))
            return None
        if mirror is not None and mirror not in mirs.keys(): return None
        if mirror in mirs.keys():
            tryhost = [mirs[mirror]]
        else:
            tryhost = [] # sort by hoster and language.
            for l in ("DE", "EN+de", "EN"):
                for h in self.Hosters:
                    tryhost.extend([mirs[m] for m in mirs.keys() if h in m and m.startswith(l+" ")])
        
        for mir in tryhost:
            output("Loading %s from %s" % (" - ".join(serpath), mir))
            mir = redirected(mir) # TODO: move this to getStream
            output("Loading %s from %s" % (" - ".join(serpath), mir))
            print "DECODED", mir
            streamurl = streamhoster.findParser(mir, output)
            if streamurl is not None: return streamurl
        output("No suitable stream found")
        return None

class Metastream(Streamsite):
    # Parserclasses to use
    Parsers = (Serienstream, Burningseries)
    
    def __init__(self):
        self.URL = ", ".join([x.__name__ for x in self.Parsers])
        self.sd = OD()
        self._doThreads(self._initParsers)
        # TODO: merge dicts
        self.genDict = OD()
        self.serDict = OD()
        unigen = set()
        for sd in self.sd.values(): unigen = unigen.union(sd.genDict.keys())
        for k in sorted(unigen):
            self.genDict[k] = OD()
            for n, sd in self.sd.items():
                if k not in sd.genDict: continue
                for sk, sv in sd.genDict[k].items():
                    if sk not in self.genDict[k]: self.genDict[k][sk] = OD()
                    self.genDict[k][sk][n+"URL"] = sv["URL"]
                    self.serDict[sk] = self.genDict[k][sk]
    
    def _initParsers(self, what, n=3):
        if n <= 0: raise RuntimeError("Loading %s failed." % what.__name__)
        try:
            self.sd[what.__name__] = what()
        except RuntimeError:
            n-=1
            print what.__name__, "Failed. Retries:", n
            time.sleep(1)
            self._initParsers(what, n)
    
    def _doThreads(self, function, targs=()):
        """
        Starts the given function (and optional arguments) for each Parser in a
        thread. returns when everybody's finished.
        """
        thr = [Thread(target=gobject.idle_add, args=(function, p)+targs) for p in self.Parsers]
        for t in thr: t.setDaemon(True)
        for t in thr: t.start()
        # we just idle-added the threads, so to really start them, we must iterate the gtk-mainloop
        while gtk.events_pending(): gtk.main_iteration()
        for t in thr: t.join()
        # and than we must wait for them to finish.
        while gtk.events_pending(): gtk.main_iteration()
    
    def _getSeasons(self, what, serie):
        self.sd[what.__name__].getSeasons(serie)
    
    def getSeasons(self, serie):
        """
        Add a description and a list of seasons to the dict of a given series
        (if it isn't there already):
        self.serDict[serie] = OD {
            "URL": "http://example.com/link/to/series",
            "Description": "Once upon a time",
            "Season 1": {
                "URL": "http://example.com/link/to/season-1"
                "Episodes": OD {} # will be filled by getEpisodes(),
            }
            "Season 2": {}, ...
        }
        also return a list of seasons (strings)
        """
        if serie not in self.serDict.keys(): return None
        if "Description" not in self.serDict[serie].keys():
            self._doThreads(self._getSeasons, (serie,))
            descr = OD([(k, v.getDescription(serie)) for k,v in self.sd.items()])
            r = OD()
            for k,v in descr.items():
                if v not in r: 
                    r[v] = k
                else:
                    r[v] = ", ".join((r[v], k))
            self.serDict[serie]["Description"] = "\n\n".join([v+":\n\n"+k for k, v in r.items()])
            
            # Merge seasons
            for n, v in self.sd.items():
                if serie not in v.serDict: continue
                xd = v.serDict[serie]
                for sk in xd.keys():
                    if not sk.startswith("Season"): continue
                    if sk not in self.serDict[serie]: self.serDict[serie][sk] = OD()
                    self.serDict[serie][sk][n+"URL"] = xd[sk]["URL"]
        sea = [x for x in self.serDict[serie].keys() if x.startswith("Season")]
        #if len(sea) == 0:
        #    # failed. remove Description to allow try again
        #    del self.serDict[serie]["Description"]
        return sea
    
    def _getEpisodes(self, what, serie, season):
        self.sd[what.__name__].getEpisodes(serie, season)
    
    def getEpisodes(self, serie, season):
        sdss = self.serDict[serie][season]
        if "Episodes" in sdss: return sdss["Episodes"].keys()
        sdss["Episodes"] = OD()
        self._doThreads(self._getEpisodes, (serie, season))
        # Merge episodes
        for n, v in self.sd.items():
            if serie not in v.serDict or season not in v.serDict[serie]: continue
            xd = v.serDict[serie][season]["Episodes"]
            for sk in xd.keys():
                if sk not in sdss["Episodes"]: sdss["Episodes"][sk] = OD()
                sdss["Episodes"][sk][n] = v.serDict[serie][season]["Episodes"][sk]
        return self.serDict[serie][season]["Episodes"].keys()
    
    # we could thread getMirrors as well, but at the moment only one streamsite
    # has to do an additional request so it wouldn't speed things up anyway.
    def getMirrors(self, serpath):
        mio = self.serDict[serpath[0]][serpath[1]]["Episodes"][serpath[2]]
        if "Mirrors" in mio: return mio["Mirrors"]
        mirs = OD()
        for n, v in self.sd.items():
            smirrors = v.getMirrors(serpath)
            if smirrors is None: continue
            for mi in smirrors.keys():
                mirs[n+" "+mi] = (v, mi)
        mio["Mirrors"] = mirs # contains: {key: (instance, mirrorkey), ...}
        return mirs
    
    def getStream(self, serpath, output=stderr.write, mirror=None):
        # order by Streamsite.Hosters, return on first success
        semi = self.getMirrors(serpath)
        if mirror is None:
            for h in self.Hosters:
                h = h.split(".")[0]
                for k in semi.keys():
                    if h in k.lower():
                        resi = semi[k][0].getStream(serpath, output, semi[k][1])
                        if resi is not None: return resi
        else:
            mi = semi[mirror]
            return mi[0].getStream(serpath, output, mi[1])


def example():
    # from plugins.bsto.streamsite import *
    
    bs = Serienstream()
    xx = (u'Scrubs - Die Anf\xe4nger', u'Season 1', u'9 Mein freier Tag')
    sea, epi = bs.getSeasons(xx[0]), bs.getEpisodes(xx[0], xx[1])
    lnks = bs.getMirrors(xx)
    
    bs.getStream(xx, mirror="Vivo")
    
    "http://serienstream.to/out/2100/678595"
    
    # TODO: This does work well in a GTK-App but not in terminal.
    # I don't know why, should investigate.
    # It fails mainly on Serienstream, WebkitScraper seems to be the problem.
    # Probably some strange gtk-gobject-thread-racetime-condition.
    ms = Metastream()
    print ms

    sea = ms.getSeasons("24")
    print "Seasons:", ", ".join(sea)
    
    eps = ms.getEpisodes("24", "Season 3")
    print eps

    lnks = ms.getMirrors(("24", "Season 3", "Tag 3: 17.00 Uhr - 18.00 Uhr"))
    for k in sorted(lnks.keys()): print k,"\t",lnks[k]

    strm = ms.getStream(("24", "Season 3", "Tag 3: 17.00 Uhr - 18.00 Uhr"))
    os.system("vlc "+strm)

