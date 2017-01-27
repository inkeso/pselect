#!/usr/bin/python2
# -*- coding: utf-8 -*-

import re, sys, time, gtk

class ProgressBar:
    """
    First parameter 'max' is needed and should be set to the highest value
    of the counter in the main-loop.
    The second and third and fith parameter are ignored (just kept to remain compatible 
    with the terminal-progressbar).
    With fourth parameter, the progressbar can be turned into a working-indicator
    when you don't know how many iterations your long-lasting-operation take.
    this can be set to true or to an integer specifying the width of the pulsating block
    """
    def __init__(self, maxi, width=0, term_stream=None, pulse=False, forceUTF=False):
        self.__PULSE = pulse
        self.__STARTTIME = time.time()
        self.__MAXI = maxi

        self.win = gtk.Window(gtk.WINDOW_POPUP)
        self.win.set_title("Waiting...")
        # 2/3 screenwidth und 1/9 height. This fails on xinerama.
        maw = self.win.get_screen().get_width() / 3 * 2
        mah = self.win.get_screen().get_height() / 9
        self.win.set_size_request(maw, mah)
        self.win.set_position(gtk.WIN_POS_CENTER)
        self.win.set_border_width(10)
        self.win.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=9000))
        self.pbar = gtk.ProgressBar()
        self.etalabel = gtk.Label("?")
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.etalabel)
        self.vbox.pack_start(self.pbar)
        self.win.add(self.vbox)
        self.win.show_all()
        if pulse and type(pulse) == int:
            self.pbar.set_pulse_step(pulse/100.0)
        while gtk.events_pending(): gtk.main_iteration()
        
    def reset(self):
        self.pbar.set_fraction(0.0)
        
    """
    This should be called in the main loop to update the progress.
    First parameter should be 0 <= cur <= max
    The should be no other output to terminal between the successive
    calls to this function.
    if cur==max, the progress is finished.
    If the loop finished before cur==maxi, you should re-call this
    functionwidth the max-value, to reset colors and place the cursor below the progressbar.
    You can change the max-value every time, if necessary.
    """
    def updateprogressbar(self, curr, cstate="", maxi=0):
        if maxi > 0: self.__MAXI=maxi
        if self.__PULSE:
            self.pbar.pulse()
            self.pbar.set_text(cstate)
            self.etalabel.set_text("?")
        elif curr < self.__MAXI:
                # calculate elapsed and estimated time
                eta = 0
                if curr > 0:
                    eta = (time.time() - self.__STARTTIME) * (self.__MAXI - curr) / curr
                etas = time.strftime("%H:%M:%S", time.gmtime(eta))
                if eta > 86400: etas = "%d days, %s" % (eta/86400, etas)
                infos = "%5.1f%% (%d/%d) [ETA: %s]" % (100.0*curr/self.__MAXI, curr, self.__MAXI, etas)
                fr = float(curr)/float(self.__MAXI)
                # fancy!
                self.win.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=int(9000*(1-fr)), blue=int(28000*fr), green=int(12000*fr)))
                self.pbar.set_fraction(fr)
                self.etalabel.set_text(infos)
                self.pbar.set_text(cstate)
        if curr == self.__MAXI:
            self.win.destroy()
        while gtk.events_pending(): gtk.main_iteration()

if __name__ == '__main__':
    n=range(1000)
    bla=ProgressBar(max(n), 70)
    start=time.time()
    for i in n:  # 0...999
        bla.updateprogressbar(i,"doo")
        time.sleep(0.01)
    
    
    #~ n=range(300)
    #~ bla=ProgressBar(1, pulse=True, forceUTF=True) # write pulsebar with max. width to stdout
    #~ time.sleep(0.1)
    #~ for i in n:  # 0...999
        #~ bla.updateprogressbar(0,"dooing...?")
        #~ time.sleep(0.06)
        
    #~ bla.updateprogressbar(1)
    
    print "fenster zu, bisschen warten"
    time.sleep(.1)
