#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re, time, urllib2, os, sys
from urllib import urlencode
from threading import Thread

def stdout(message): # print as a function...
    print message


def simpleStreamhost(url, output, okbutton, waittime, filere, bonusformfields=[], debug=False):
    """
    some streamhosters work the same way:
    - GET-request to streamurl (1. parameter)
      (2nd parameter output is a function with a single parameter (str) for printing messages)
    - check for "OK" or "continue" button (regExp "okbutton")
    - collect all form-fields (hidden inputs)
    - also some sites use javascript to inject additional fields
      (6. parameter, a list (of a mix) of:
        - regexps (str) with 2 groups (name, value) to catch them)
        - tuples with (name, value)
    - wait a couple of seconds ("waittime" can be regExp (first matching group) or int)
    - POST request to streamurl, with form-fields as data
    - fetch media-url (regExp "filere", first matching-group should be the file)
    """
    hoster = re.search('https?://(.+?)/.*', url).group(1)
    # first request: GET
    heads = {'User-agent':'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
    req = urllib2.Request(url, headers=heads)
    response = urllib2.urlopen(req)
    content = response.read()
    url = response.geturl() # update URL (if redirected)
    cook = response.headers.getheader("set-cookie")
    response.close()
    if debug: output("GET to URL: "+url+"\nCOOKIE: "+cook+"\n")
    
    heads['Referer'] = url
    heads['Cookie'] = cook
    
    if not re.search(okbutton, content):
        output('Datei nicht gefunden')
        if debug: output("RESPONSE:\n"+content)
        return None
    
    # get regular form-values
    fvals = {}
    
    for i in re.finditer('<input.*?name="(.*?)".*?value="(.*?)"', content):
        fvals[i.group(1)] = i.group(2)
    
    # bonusfields
    for bf in bonusformfields:
        if type(bf) is str:
            for i in re.finditer(bf, content):
                fvals[i.group(1)] = i.group(2)
        if type(bf) is tuple:
            fvals[bf[0]] = bf[1]
    
    data = urlencode(fvals)
    
    if type(waittime) is str: # waittime can be a regexp.
        waittime = int(re.search(waittime, content).group(1)) + 1
    for x in range(waittime):
        output('Warte auf %s\n%d' % (hoster, waittime-x))
        time.sleep(1)
    
    if debug: output("POST to URL: "+url+"\nDATA: "+data+"\nCOOKIE: "+cook+"\n")
    
    # second request: POST
    req = urllib2.Request(url, data=data, headers=heads)
    response = urllib2.urlopen(req)
    rtxt = response.read()
    response.close()
    findurl = re.search(filere, rtxt)
    if not findurl:
        output('Datei nicht gefunden')
        if debug: output("RESPONSE:\n"+rtxt)
        return None
    return findurl.group(1)

def getYtdl():
    """check whether youtube-dl is bundled or installed and return its full path"""
    # try same directory (bundled)
    ytdl = os.path.join(sys.path[0],"youtube-dl") 
    if os.path.isfile(ytdl): return ytdl
    # try path (installed)
    for path in os.environ["PATH"].split(os.pathsep):
        ytdl = os.path.join(path.strip('"'), "youtube-dl")
        if os.path.isfile(ytdl): return ytdl
    return False

def _ytdlthread(ytdl, url, fifo):
    os.system(ytdl+" -o '%s' --no-call-home '%s'" % (fifo, url))
    print "YTDL finished. Killing pipe."
    # when download finished or player exited, terminate & remove (broken) pipe.
    os.system("echo > '%s'" % fifo)
    os.system("rm '%s'" % fifo)
    return True

def ytdlStreamhost(url, output, debug=False):
    """
    use youtube-dl to get video from supported hoster (see ./youtube-dl --list-extractors).
    You need latest youtube-dl installed or bundled.
    """
    
    # create fifo and start downloading (in a thread)
    FIFO="/tmp/ytdlfifo"
    # take care of debris (ytdl sometime creates Frag-files)
    os.system("rm "+FIFO+"*")
    #os.unlink(FIFO)
    os.system("mkfifo '%s'" % FIFO)
    output("Start youtube-dl...")
    thr = Thread(target=_ytdlthread, args=(getYtdl(), url, FIFO))
    thr.setDaemon(True)
    thr.start()
    # return fifo as uri. Download will work as well as playing. Sweet.
    return "file://"+FIFO

def jdStreamhost(url, output, debug=False):
    """
    -- CURRENTLY NOT IN USE --
    Use JDownloader to decrypt/load videos.
    Currently unused in favor of youtube-dl
    """
    # TODO: JDownloader zum decrypten / laden

    # Source:  svn co svn://svn.jdownloader.org/jdownloader
    # MyJD-API: https://support.jdownloader.org/Knowledgebase/Article/View/40/0/myjdownloaderorg-api-docu
    
    # 0- Dieses Funktion muss man konfigurieren können. Es wäre gut, das nicht
    # hier hardcoded zu machen.
    
    # 1- Bei den hoster-plugins was abgucken oder verwenden. Wäre die schönste 
    # Lösung, weil man keine laufende JD-Instanz bräuchte, man braucht auf jeden
    # Fall aber nicht nur den decrypteten Link, sondern muss wirklich via JD 
    # laden. Sieht also nicht so einfach aus.
    
    # 2- JD-plugin basteln, daß auf TCP-connections hört und uns das Hinzufügen
    # und Starten von Links ermöglicht und den vollen Pfad zur *.part-Datei
    # zurückgibt, wenn der Download läuft. Und evtl. das Löschen der Zieldatei
    # ermöglicht.

    # 3- JD über die offizielle MyLD-API ansprechen. Nicht unelegant. Vielleicht
    # kann man darüber sogar hinter aufräumen. Ist aber nicht soo einfach (siehe
    # docs) und außerdem läuft das dann über deren Server, das finde ich doof
    # und unnütz, man muss den JD ja eh lokal haben, warum soll ich den über
    # deren Server ansprechen?
    
    # 4- Quick-and-dirty das "folderwatch"-Plugin von JD verwenden.
    # Zuerst im JD: Plugin installieren & konfigurieren (Pfad, Poll-interval)
    # Bei den Advanced Settings noch LinkgrabberSettings: Auto Confirm Delay auf
    # weniger setzen. 
    # TODO: Prüfen, ob JD läuft und ggf. starten
    
    # dann in dem folderwatch-Ordner eine "temp.crawljob" anlegen.
    watchfile="/opt/JD2/watch/temp.crawljob"
    filename=re.sub("[^A-Za-z0-9.-]", "_",re.sub("https?://", "", url))
    wf = open(watchfile, "w")
    wf.write('''
        text=%s
        autoStart=TRUE
        forcedStart=TRUE
        filename=%s
        packageName=serien
        autoConfirm=TRUE
        enabled=TRUE
    ''' % (url, filename))
    wf.close()
    # Auf download warten, also bis die entsprechende *.part-Datei eine gewisse 
    # Größe hat, dann den Pfad zu ihr zurückgeben.
    partfile="/home/iks/Downloads/serien/%s.part" % filename
    uptime = 120 # Nach einer Minute geben wir auf
    while uptime > 0 and (not os.path.exists(partfile) or os.stat(partfile).st_size < 4096*1024):
        output("Warte auf JDownloader (%d)" % (uptime/2))
        uptime -= 1
        time.sleep(.5)
    
    # Nachteil 1: Wer räumt hinterher auf?
    # Nachteil 2: Man muss sowohl JD als auch hier penibel konfigurieren.
    if uptime <= 0:
        return None
    else:
        return partfile

def listHosters(htyp=None):
    """
    List supported hosters for a parsertype. or all, if no type is given.
    """
    if htyp and htyp in _hoster:
        return _hoster[htyp]["hoster"].keys()
    else:
        result = []
        [result.extend(x["hoster"].keys()) for x in _hoster.values()]
        return result

def checkParser(url):
    """
    Just check, whether a parser is available
    """
    chost = url.lower()
    try: chost = re.search('https?://(www\\.)?(.+?)/.*', url.lower).group(2)
    except: pass
    for v in _hoster.values():
        if chost in v['hoster'] and v['function'] is not None:
            return True
    return False

def findParser(url, output=stdout, debug=False):
    """
    Find / generate parser based on base-URL
    """
    chost = re.search('https?://(www\\.)?(.+?)/.*', url).group(2)
    link = None
    for v in _hoster.values():
        if chost in v['hoster'] and v['function'] is not None:
            link = v['function'](url, output, *v['hoster'][chost], debug=debug)
            break
    else:
        output("No suitable parser found for "+chost)
    return link



_hoster = {
    'simple' : { 'function' : simpleStreamhost, 'hoster' : {
                           # okbutton            waittime                          filere                          bonusformfields=[]
        'powerwatch.pw'  : ('id="btn_download"',  'span id="cxc">([0-9]+)</span',   '\\[{file:"(.+?)"'),
        'primeshare.tv'  : ('id="dlbutton"',      'var cWaitTime = ([0-9]+);',      'stream\',\\s+url: \'(.+?)\''),
        'promptfile.com' : ('Continue to File',   1,                                'url: \'(.+?)\','),
        'shared.sx'      : ('button id="access"', 'var RequestWaiting = ([0-9]+);', 'data-url="(.+?)"'),
        'streamcloud.eu' : ('id="btn_download"',  'var count = ([0-9]+);',          'file: "(.+?)"'),
        'thevideo.me'    : ('id="btn_download"',  1,                                '\'360p\', file: \'(.+?mp4)\'', ['\'<input/>\'.*?name: \'(.*?)\'.*?value: \'(.*?)\'', '(imhuman)()']),
        'vodlocker.com'  : ('id="btn_download"',  'span id="cxc">([0-9]+)</span',   'setup\\(\\{\\s+file: "(.+?)"'),
    }}
}

if getYtdl():
    _hoster['youtube-dl'] = { 'function' : ytdlStreamhost, 'hoster' : dict.fromkeys((
        'auroravid.to',
        'bitvid.sx',
        'cloudtime.to',
        'nowvideo.sx',
        'nowvideo.to', 
        'openload.co',
        'sharesix.com',
        'videoweed.es',
        'vidzi.tv',
        'vivo.sx',
        'vidto.me'
    ),())}
