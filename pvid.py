#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  pvid.py
#  
#  Copyright 2014 Eloi Maelzer <iks@SteroiX>
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

import os, sys, subprocess, time, re, cPickle, select, random, fractions

try:
    import scandir
    SCANDIR = True
except:
    SCANDIR = False
    print "Consider \"pip install scandir\" since it is way faster than os.listdir"

import progressbar
#from pprint import pprint

def log(s, level=0):
    '''
    colored output to console.
    specify level for increased urgency:
        0 - info (white)
        1 - success (green)
        2 - warning (yellow)
        3 - error (red)
        4 - fatal (red background)
    '''
    if level not in range(5): level = 0
    colors = ('37', '32' ,'33', '31', '37;41')
    sys.stdout.write('\033[1;{0}m>\033[0;{0}m {1}\033[0m\n'.format(colors[level], s))
    sys.stdout.flush()

class InfoBackend:
    '''
    Base-Class for movieinfo-collecting classes (with the help of external 
    programms). This class can also be used as a dummy to not get movieinfos at
    all.
    '''
    # these 4 tags _must_ be in the result-dict and type(int)
    inttags = ('ID_LENGTH', 'ID_VIDEO_WIDTH', 'ID_VIDEO_HEIGHT', 'ID_AUDIO_NCH')
    # additional tags may be present and of type(str).
    strtags = ('ID_VIDEO_CODEC', 'ID_VIDEO_BITRATE', 'ID_VIDEO_ASPECT', 'ID_VIDEO_FPS',
               'ID_AUDIO_CODEC', 'ID_AUDIO_BITRATE', 'ID_AUDIO_RATE')
    
    def get(self, filename):
        '''
        a derived class should overwrite this method.
        
        return a dict at least containing all inttags (keys) with ints of the
        corresponding values.
        '''
        return dict([(x, 0) for x in self.inttags])
    
    def testdir(self, directory="."):
        '''get info for each file in current dir. list them pretty.'''
        print "%-50s\t" % "FILENAME","\tResolution\t Length\tCh"
        for t in self.strtags: print t,"\t",
        print
        
        for f in os.listdir(directory):
            print "%-50s\t" % f,
            try:
                m = self.get(f)
                for j in self.strtags: 
                    if j not in m: m[j] = "?"
                print "\t%dx%d\t" % (m['ID_VIDEO_WIDTH'], m['ID_VIDEO_HEIGHT']),
                print sec2hms(m['ID_LENGTH']), "\t", m['ID_AUDIO_NCH'],
                for t in self.strtags: print "\t", m[t],
            except Exception as e:
                print e,
            print
    
    def close():
        pass

class MplayerInfo(InfoBackend):
    '''
    Invisible Mplayer Slave for info (playlength) retrival.
    '''
    # sometimes length is not available immediately (worst case: after 
    # playing the hole thing). Only try this number of seconds:
    timeout = 10
    
    def __init__(self):
        self.orcus = open('/dev/null', 'w')
        self._mplayer = subprocess.Popen(['mplayer', '-nomsgcolor','-nomsgmodule', 
                                          # -vo null won't work with some codecs, so we actually display the frames. small.
                                          '-geometry', '1x1', '-fixed-vo', '-frames', '1',
                                          '-ao', 'null', '-channels', '6',
                                          '-slave', '-identify', '-idle', '-quiet'],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.orcus, bufsize=0)
        self.eoftag = 'ID_EXIT'
    
    def get(self, filename):
        result = dict([(x, 0) for x in self.inttags])
        self._mplayer.stdin.write('pausing loadfile "%s"\n' % filename)
        
        while any(select.select([self._mplayer.stdout], [], [], self.timeout)):
            l = self._mplayer.stdout.readline().strip().split("=", 1)
            if l[0] in self.inttags and not result[l[0]]:
                    result[l[0]] = int(float(l[1]))
            xit = l[0] == self.eoftag
            if xit and l[1] != "EOF": print "MPlayer EXIT", l[1]
            if all(result.values()) or xit:
                # early break. but we have to read remaining lines from mplayer.
                # we use a much smaller timeout here
                while any(select.select([self._mplayer.stdout], [], [], .1)):
                    self._mplayer.stdout.readline()
                return result 
        return result
    
    def close(self):
        self._mplayer.stdin.write('quit\n')
        self._mplayer.communicate()
        self.orcus.close()

class OmxplayerInfo(InfoBackend):
    def __init__(self):
        # throw exception on init, if omxplayer doesn't exist
        subprocess.check_output(['which', 'omxplayer'], stderr=subprocess.STDOUT)
        
    def get(self, filename):
        result = dict([(x, 0) for x in self.inttags])
        try: # omxplayer returns with exitcode 1. always.
            mi = subprocess.check_output(['omxplayer','-i', filename], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            mi = e.output
        # Obligatory
        dusu = re.search(".*Duration: ([0-9:]+).*", mi, flags=re.DOTALL)
        if dusu: result['ID_LENGTH'] = hms2sec(dusu.group(1))
        resi=(0,0)
        resx = re.search(".* ([0-9]+x[0-9]+)[, ].*", mi, flags=re.DOTALL)
        if resx: resi = resx.group(1).split('x')
        try:    result['ID_VIDEO_WIDTH'] = int(resi[0])
        except: pass
        try:    result['ID_VIDEO_HEIGHT'] = int(resi[1])
        except: pass
        if "mono" in mi: result['ID_AUDIO_NCH'] = 1
        if "stereo" in mi: result['ID_AUDIO_NCH'] = 2
        if "2 channel" in mi: result['ID_AUDIO_NCH'] = 2
        if "5.1" in mi: result['ID_AUDIO_NCH'] = 6
        # Additional
        pairs = (
            ('ID_VIDEO_CODEC'  , ".*Video: ([^ ,]+).*"),
            ('ID_VIDEO_BITRATE', ".* bitrate: ([0-9]+ kb/s).*"),
            ('ID_VIDEO_ASPECT' , ".* DAR ([0-9:]+).*"),
            ('ID_VIDEO_FPS'    , ".* ([0-9.]+) fps,.*"),
            ('ID_AUDIO_CODEC'  , ".*Audio: ([^ ]+) .*"),
            ('ID_AUDIO_BITRATE', ".*Audio:.+? ([0-9]+ kb/s).*"),
            ('ID_AUDIO_RATE'   , ".* ([0-9]+ Hz), .*")
        )
        for i,r in pairs: 
            src = re.search(r, mi, flags=re.DOTALL)
            if src: result[i] = src.group(1)
        return result
    
    def close(self): pass

class MediainfoInfo(InfoBackend):
    def __init__(self):
        # throw exception on init, if mediainfo doesn't exist
        subprocess.check_output(['which', 'mediainfo'], stderr=subprocess.STDOUT)
    
    def get(self, filename):
        result = dict([(x, 0) for x in self.inttags])
        # 4831000 720 400 XviD 888867 1.800 25.000
        cmd = ['mediainfo', '--Inform=Video;%Duration% %Width% %Height% %CodecID/Hint% %BitRate% %DisplayAspectRatio% %FrameRate%']
        miV = subprocess.check_output(cmd + [filename], stderr=subprocess.STDOUT).split(" ")
        # 2 ADPCM 352800 44100
        cmd = ['mediainfo', '--Inform=Audio;%Channels% %Format% %BitRate% %SamplingRate%']
        miA = subprocess.check_output(cmd + [filename], stderr=subprocess.STDOUT).split(" ")
        # Obligatory
        try: result['ID_LENGTH'] = int(float(miV[0]) / 1000)
        except: pass
        try: result['ID_VIDEO_WIDTH'] = int(miV[1])
        except: pass
        try: result['ID_VIDEO_HEIGHT'] = int(miV[2])
        except: pass
        try: result['ID_AUDIO_NCH'] = int(miA[0])
        except: pass
        if len(miV) > 3:
            # Additional
            result['ID_VIDEO_CODEC'] = miV[3]
            try: result['ID_VIDEO_BITRATE'] = "%d kb/s" % (float(miV[4]) / 1000)
            except: pass
            try:
                fxx = fractions.Fraction(float(miV[5])).limit_denominator() # I f'ckn love python. This could be a real PITA.
                result['ID_VIDEO_ASPECT' ] = "%d:%d" % (fxx.numerator, fxx.denominator)
            except:
                pass
            try: result['ID_VIDEO_FPS'    ] = "%.1f" % float(miV[6])
            except: pass
        if len(miA) > 1:
            result['ID_AUDIO_CODEC'  ] = miA[1]
            try: result['ID_AUDIO_BITRATE'] = "%.1f kb/s" % (float(miA[2]) / 1000)
            except: pass
            try: result['ID_AUDIO_RATE'   ] = "%.1f kHz" % (float(miA[3]) / 1000)
            except:pass
        return result
    
    def close(self): pass

class ExiftoolInfo():
    pass ## TODO

class Videos():
    def __init__(self, 
                 srcdir=None, 
                 cache='.pvidcache', 
                 rex='\.(wmv|mpe?g?|avi|ogv|asf|mov|flv|mp4|m[4k]v|webm|vob|divx)$',
                 verbose=True,
                 clearcache=True,
                 infobackend=None):
        '''
        scan srcdir recursively for all videofiles (filnames matching rex)
        if srcdir is None, the current dir will be used.
        if cachefile starts with a slash or tilde, it is an absolulte path.
        '''
        self.verbose = verbose
        self.srcdir = srcdir or '.'
        self.rex = re.compile(rex, re.I)
        self.pb = None # may contain a progressbar-object
        self.total = { 'vLen':0, 'files':0, 'size':0 }
        self.files = [] # a recursive list of all videofiles and dirs
        
        # try to load cache
        cache = os.path.expanduser(cache)
        if not os.path.isabs(cache):
            cache = os.path.join(srcdir, cache)
        try:
            with open(cache, 'r') as cf:
                self.cache = cPickle.load(cf)
        except:
            self.cache = {}
            # cache is a dict of dicts with video-properties: 
            # {"full/path/to.avi" : {'ID_LENGTH': 1220.0, 'ID_VIDEO_WIDTH': 320, ...}
            # see MPlayerInfo.get() for details
        
        # get filetree
        if verbose: 
            log('Reading directory tree »%s«' % self.srcdir, 1)
            self.pb = progressbar.ProgressBar(1, pulse=1, term_stream=sys.stderr)
        self.files, self.total = self.dir2infolist(srcdir)
        if verbose: 
            self.pb.updateprogressbar(1, 'Done: %d files found. (%s, %s)' % 
                (self.total['files'], byte2hr(self.total['size']), sec2hms(self.total['vLen'])))
            self.pb = None
        
        def flatten(items):
            '''recursion.
            get flat list of all a) files with unknown playtime and
            b) all files in tree.'''
            lifo = [] # missing in cache (files only)
            defo = [] # all files
            for x in items:
                if 'items' in x: # is a dir; recursion
                    subf = flatten(x['items'])
                    lifo.extend(subf[0])
                    defo.extend(subf[1])
                else:
                    if x['vLen'] == -1: lifo.append(x['fullPath'])
                    defo.append(x['fullPath'])
            return (lifo, defo)
        lifo, defo = flatten(self.files)
        # filenames which are in (loaded) cache and NOT in the filesystem
        obfo = filter(lambda x: x not in defo, self.cache.keys())
        # copy self.cache. tmpcache will contain all entries from loaded
        # cache-file (and the new ones) including potentially missing files
        # while self.cache is reduced to items existing in filetree.
        tmpcache = dict(self.cache.items())
        if len(obfo) > 0: # remove old / nonexisting items from cache
            log("%d files in cache, but not on disk" % len(obfo),2)
            # reduce cache
            self.cache = dict(filter(lambda x: x[0] in defo, self.cache.items()))
        
        # get the playtime and dimension of items missing in cache
        if len(lifo) > 0: # got new files!
            if infobackend:
                mpl = infobackend()
            else:
                mpl = None
                for c in (OmxplayerInfo, MediainfoInfo, MplayerInfo):
                    try: 
                        mpl = c()
                        break
                    except:
                        continue
                else:
                    raise Exception("No suitable mediainfo-tool found. Please install mediainfo, mplayer or omxplayer")
            
            if verbose: 
                mpb = re.sub("<pvid\\.(.+?)Info .*", "\\1",str(mpl))                
                log("getting metadata for %d files (using %s)" % (len(lifo), mpb), 1) # Which InfoBackend used?
                self.pb = progressbar.ProgressBar(len(lifo), 0, sys.stderr)
            for i in range(len(lifo)):
                if verbose: self.pb.updateprogressbar(i, lifo[i][len(self.srcdir)+1:])
                try:    
                    tmpcache[lifo[i]] = mpl.get(lifo[i])
                    self.cache[lifo[i]] = tmpcache[lifo[i]]
                except: print "Getting mediainfo failed:", lifo[i]
            
            mpl.close()
            # copy playtimes from cache to filetree
            self.files, self.total['vLen'] = self.reassign(self.files)
            if verbose: 
                self.pb.updateprogressbar(len(lifo),'Done. Total is now %s' % sec2hms(self.total['vLen']))
                zero = dict(filter(lambda x: x[1]['ID_LENGTH']==0, tmpcache.items()))
                if len(zero) > 0:
                    log('unknown length for %d items' % len(zero), 2)
                    # for p in zero.keys(): log(p[len(self.srcdir)+1:])
            self.pb = None
        
        if len(lifo) > 0 or (len(obfo) > 0 and clearcache): # cache modified. save.
            with open(cache, 'w') as cf:
                if clearcache:
                    cPickle.dump(self.cache, cf, 0)
                    log('Missing files have been removed from cache', 2)
                else:
                    cPickle.dump(tmpcache, cf, 0)
                    log('Missing files are kept in cache', 2)
            log('Times saved to %s' % cache, 1)
        

    def reassign(self, tree):
        '''recursively reassign playtimes in tree from cache'''
        result = []
        for dr in tree:
            if 'items' in dr: # is a dir; recursion
                dr['items'], dr['vLen'] = self.reassign(dr['items']) 
            elif dr['vLen'] == -1: 
                ifc = self.cache[dr['fullPath']]
                # TODO: Alles an Medieninfo (kann variieren) hier reintun, als dict
                dr['vLen'] = ifc['ID_LENGTH']
                dr['dim'] = (ifc['ID_VIDEO_WIDTH'], ifc['ID_VIDEO_HEIGHT'])
                dr['aCh'] = ifc['ID_AUDIO_NCH']
            result.append(dr)
        return result, sum(x['vLen'] for x in tree)
    
    def dir2infolist(self, sDir, filefilter = None):
        '''
        scan directory for dirs & files. return a recursive list of dicts:
        [{
          fullPath=str, (the videofile or directory)
          fileName=str, (the display-name, filename without extension)
          items=[],     (if it is a dir, subdirs & files are here (same format))
          size=int,     (size in bytes for files and directories (file sum).)
          files=int     (number of files; only for directories)
          mTime=str,    (representation of last modification-date of the file/dir)
          vLen=int      (length of the video in seconds. cummulated for dirs)
          dim=(int,int) (tuple of video-dimensions (width, height; only for files)
          aCh=int       (Number of audio channels; only for files)
        }, ...]
        vLen will be filled from cache only here. Files missing in cache get -1.
        '''
        
        dl = scandir.scandir(sDir) if SCANDIR else os.listdir(sDir)
        # do not update progressbar: since reading filetree is fast (especially
        # with scandir) gtk-update may be significant overhead.
        # self.pb.updateprogressbar(0,sDir)
        dirs=[]
        files=[]
        for fentry in dl:
            fnam = fentry.name if SCANDIR else fentry
            if fnam[0] == '.': continue         # ignore hidden files
            if fnam == 'lost+found': continue   # ignore journal
            nKey = fentry.path if SCANDIR else os.path.join(sDir, fnam)
            fStat = fentry.stat() if SCANDIR else os.stat(nKey)
            # time.strftime('%d %b %Y %H:%M', time.gmtime(fTime))
            if fStat.st_mode & 2**14: # is dir
                dirs.append({
                    'fullPath': nKey,
                    'fileName': fnam,
                    'items': [],
                    'size': 0, 
                    'mTime': fStat.st_mtime,
                    'vLen': 0})
            elif self.rex.search(fnam): # is video
                if filefilter and filefilter not in fnam: continue
                vlen = -1
                dim = (0, 0)
                ach = 0
                if nKey in self.cache:
                    ifc = self.cache[nKey]
                    vlen = ifc['ID_LENGTH']
                    dim = (ifc['ID_VIDEO_WIDTH'], ifc['ID_VIDEO_HEIGHT'])
                    ach = ifc['ID_AUDIO_NCH']
                files.append({
                    'fullPath': nKey,
                    'fileName': fnam,
                    #'items': [],
                    'size': fStat.st_size, 
                    'mTime': fStat.st_mtime,
                    'vLen': vlen,
                    'dim': dim,
                    'aCh': ach})
        
        if len(dirs) > 0:
            dirs.sort(cmp=lambda x,y: (x['fileName'].lower()>y['fileName'].lower())*2-1)
            for d in range(len(dirs)):
                dirs[d]['items'], ntot = self.dir2infolist(dirs[d]['fullPath'], filefilter)
                dirs[d]['size'] = ntot['size']
                dirs[d]['vLen'] = ntot['vLen']
                dirs[d]['files'] = ntot['files']
        # remove empty dirs
        dirs = filter(lambda x: len(x['items']) > 0, dirs)
        files.sort(cmp=lambda x,y: (x['fileName'].lower()>y['fileName'].lower())*2-1)
        # calculate totals
        both = dirs + files
        tot = {'vLen': sum([x['vLen'] for x in both]),
               'size': sum([x['size'] for x in both]),
               'files': len(files) + sum([x['files'] for x in dirs])}
        return (both, tot)
    
    def filteredfiles(self, txt):
        '''
        return a reduced/filtered version of self.files
        '''
        return self.dir2infolist(self.srcdir, filefilter=txt)
    
    def getAll(self, path):
        '''
        return a list of all videos (filenames) below a given path (may be a
        directory or file)
        [[filename, 0, length, audiochannels], ...]
        '''
        # lazy version (most likely not the correct order)
        files = filter(lambda x: x.startswith(path), self.cache.keys())
        files.sort()
        return [[x, 0, self.cache[x]['ID_LENGTH'], self.cache[x]['ID_AUDIO_NCH']] for x in files]
    
    def getSnippet(self, path, sl):
        '''
        return a random snippet with (at most) sl seconds playtime.
        [filename, start, length, audiochannels] or None if the file does not exist in cache
        '''
        if not path in self.cache: return None
        l = self.cache[path]['ID_LENGTH']
        if l > sl: # videolength exceeds max. snippet-length. 
            ss = random.randint(0, l-sl) # set random startpoint.
            return [path, ss, sl, self.cache[path]['ID_AUDIO_NCH']]
        else:
            return [path, 0, l, self.cache[path]['ID_AUDIO_NCH']] # full file
    
    def getRandom(self, path, sublength, totlength):
        '''
        return a random list of video-snippets in `path`:
        [[filename, start, length, audiochannels], ...]
        where length is an most `sublength` and the total length won't
        exceed `totlength` (seconds).
        start (seconds) will be randomly assigned
        
        if path is a file, `totlength` is ignored and the result contains
        one random snippet of this file (see self.getSnippet())
        '''
        if path in self.cache: 
            return [self.getSnippet(path, sublength)]
        else:
            pofi = filter(lambda x: x.startswith(path), self.cache.keys())
            tot = totlength
            res = []
            while tot > 0:
                nu = self.getSnippet(random.choice(pofi), min(sublength, tot))
                res.append(nu)
                tot -= nu[2]
            return res

class Playlist():
    '''
    Contains a playlist and a playcommand.
    Can create a playlist-file (write a shellscript and start it).
    TODO: omxplayer oder mplayer?
    '''
    
    def __init__(self, parameters=""):
        self.parameters = parameters # "global" parameters for mplayer
        self.playlist = [] # contains entries in the form [filename, from, to, fileparameters]
    
    def additem(self, filename, start=-1, length=-1, parameters=""):
        # mplayer-parameters specifically for this item
        self.playlist.append([filename, start, length, parameters])
    
    def delitem(self, idx):
        self.playlist.remove(idx)
    
    def moveitem(self, idx, pos):
        '''
        take element idx and put it on pos
        moveitem(2, 4) :
        [A, B, C, D, E, F, G] ==> [A, B, D, E, C, F, G]
        '''
        tmp = self.playlist.pop(idx)
        self.playlist.insert(pos, tmp)
    
    def writeplaylist(self, filename, player='mplayer'):
        '''
        player may be mplayer, omxplayer, vlc (TODO). There may be a better way
        than to use magic strings.
        '''
        special = ['\\', '$', '`', '"'] # escape those
        with open(filename, 'w') as f:
            f.write('#!/bin/bash\n')
            if player in ('mplayer', 'mpv'):
                if len(self.playlist) > 0:
                    f.write(player+' ' + self.parameters + ' \\\n')
                    for pi in self.playlist:
                        for s in special: pi[0] = pi[0].replace(s, '\\'+s)
                        f.write('"'+pi[0]+'" ')
                        # this is mplayer-specific.
                        if pi[1] > 0: f.write('-ss %d ' % pi[1])
                        if pi[2] > 0: f.write('-endpos %d ' % pi[2])
                        # append fileparameters
                        f.write(pi[3])
                        f.write(' \\\n')
            if 'omxplayer' in player:
                # TODO: Man kann die playlist nicht unterbrechen. Das ist doof.
                for pi in self.playlist:
                    for s in special: pi[0] = pi[0].replace(s, '\\'+s)
                    fpara = ""
                    f.write(player+' '+self.parameters+' '+pi[3])
                    if pi[1] > 0: f.write('--pos '+sec2hms(pi[1], human=False))
                    if "/usb/" in pi[0]: f.write(' --vol -4000')
                    # für pi[2] wäre ein getimtes kill die einzige option.
                    # oder "Quit" über dbus →http://hackersome.com/p/popcornmix/omxplayer
                    f.write(' "'+pi[0]+'"\n')
            f.write('\n\n')
        try:
            os.chmod(filename, 0755)
        except:
            pass
        
        return filename

## Classless Helpers ##
def play(videofile, parameters="", start=-1, length=-1, player='mplayer'):
    '''just launch mplayer'''
    assert type(videofile) in (str, unicode)
    if player in ('mplayer', 'mpv'):
        if start > 0: parameters += " -ss %d" % start
        if length > 0: parameters += " -endpos %d" % length
        cmd = [player] + parameters.split() + [videofile]
    if 'omxplayer' in player:
        if start > 0: parameters += " -l "+sec2hms(start, human=False)
        if "/usb/" in videofile: parameters += "--vol -4000"
        cmd = player.split() + parameters.split() + [videofile]
    subprocess.call(cmd)

def multiplay(plfiles, masterfile, start=True):
    '''
    create a shellscript to launch several playlistscripts, waiting
    for each other
    '''
    # check max length of file against max BASH-commandline length
    maxlen = int(subprocess.Popen(["getconf", "ARG_MAX"], stdout = subprocess.PIPE).communicate()[0])
    for i in range(len(plfiles)):
        if plfiles[i] is None: continue
        filen = os.stat(plfiles[i]).st_size
        if filen > maxlen: 
            raise RuntimeError("Playlist %d (%s) too long (by %d bytes)" % (i, plfiles[i], filen-maxlen))
    
    with open(masterfile, 'w') as f:
        f.write('#!/bin/bash\n')
        for i in range(len(plfiles)):
            if plfiles[i] is None: continue
            f.write('"'+plfiles[i]+'" &\n')
            f.write('PID%d=$!\n' % i)
        f.write('\n')
        for i in range(len(plfiles)):
            f.write('wait $PID%d\n' % i)
        f.write('\n')
    if start:
        subprocess.call(['bash', masterfile])

def sec2hms(s, human=True):
    '''
    Return a string representing a human readable representation of a 
    time (seconds)
    '''
    h,m,s = (s/60/60, (s/60) % 60, s % 60)
    if not human:
        return "%d:%02d:%02d" % (h,m,s)
    if h > 24:
        return "%d days, %d:%02d:%02d" % (h/24, h%24,m,s)
    if h > 0: 
        return "%d:%02d:%02d" % (h,m,s)
    else:
        return "%02d:%02d" % (m,s)

def hms2sec(s):
    '''
    reverse of the above
    '''
    hms = s.split(":")
    hms.reverse()
    return sum([60**i * int(hms[i]) for i in range(len(hms))])

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

def getzero(cache):
    '''return a list of entries with length == 0'''
    return filter(lambda x: x[ID_LENGTH]==0, cache)

def scrubcache(cachefile):
    # load cache
    with open(cachefile, 'r') as cf: cache = cPickle.load(cf)
    # remove zero-length-items
    valid = dict(filter(lambda x: x[1]['ID_LENGTH']>0, cache.items()))
    # write cache
    with open(cachefile, 'w') as cf: cPickle.dump(valid, cf, 0)


###############################
# v=Videos('/home/iks/Workspace/Pselect/test')
# pprint (v.files)
# pprint (v.total)
# pprint (v.cache)
