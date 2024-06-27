import logging
import musicpd
import threading
import time
import wx
import wx.adv
from threading import *

logging.basicConfig(level=logging.INFO)

EVT_MPD_STATS_ID = wx.NewId()
def EVT_MPD_STATS(win, func):
    win.Connect(-1, -1, EVT_MPD_STATS_ID, func)
class MpdStatsEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_STATS_ID)
        self.data = data

EVT_MPD_STATUS_ID = wx.NewId()
def EVT_MPD_STATUS(win, func):
    win.Connect(-1, -1, EVT_MPD_STATUS_ID, func)
class MpdStatusEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_STATUS_ID)
        self.data = data

EVT_MPD_CURRENTSONG_ID = wx.NewId()
def EVT_MPD_CURRENTSONG(win, func):
    win.Connect(-1, -1, EVT_MPD_CURRENTSONG_ID, func)
class MpdCurrentSongEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_CURRENTSONG_ID)
        self.data = data
#EVT_TICK_ID = wx.NewIdRef()
#def EVT_TICK(win, func):
#    win.Connect(-1, -1, EVT_TICK_ID, func)
#class TickEvent(wx.PyEvent):
#    def __init__(self, data):
#        wx.PyEvent.__init__(self)
#        self.SetEventType(EVT_TICK_ID)
#        self.data = data

class MpdThread(threading.Thread):

    """"""
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window
        
        self.logger = logging.getLogger("MPDThread")

        self.stats = {}
        self.status = {}
        self.currentsong = {}

        self.dorefreshstats = True
        self.dorefreshstatus = True
        self.dorefreshcurrentsong = False
        
        self.running = False

    """Get a connected client"""
    def getClient(self) -> musicpd.MPDClient:
        # TODO: load from config
        host = '192.168.1.10'
        port = '6600'
        musicpd.CONNECTION_TIMEOUT = 1
        self.logger.debug("Connecting to %s:%s", host, port)
        client = musicpd.MPDClient()
        try:
            client.connect(host, port)
        except musicpd.MPDError as e:
            client = False
            self.logger.warning("Error connecting to MPD")
        return client
    
    """Stop the thread"""
    def stop(self):
        self.running = False
    """Stat the thread (override)"""
    def run(self):
        self.running = True
        while self.running:
            self.logger.debug("tick()")
            if self.dorefreshstats:
                self.dorefreshstats = False
                self.__refreshStats()
            if self.dorefreshstatus:
                self.__refreshStatus()
            if self.dorefreshcurrentsong:
                self.dorefreshcurrentsong = False
                self.__refreshCurrentSong()
            time.sleep(1)

    """Refresh the stats"""
    def refreshCurrentSong(self):
        self.dorefreshstats = True
    """Refresh the stats"""
    def __refreshStats(self):
        self.logger.debug("refreshStats()")
        cli = self.getClient()
        stats = {}
        if cli:
            stats = cli.stats()
            cli.disconnect()
        if stats != self.stats:
            self.stats = stats
            wx.PostEvent(self.window, MpdStatsEvent(self.stats))

    """Refresh the status info"""
    def __refreshStatus(self):
        self.logger.debug("refreshStatus()")
        cli = self.getClient()
        status = {}
        if cli:
            status = cli.status()
            cli.disconnect()
        if status != self.status:
            self.status = status
            wx.PostEvent(self.window, MpdStatusEvent(self.status))

    """Refresh the current song"""
    def refreshCurrentSong(self):
        self.dorefreshcurrentsong = True
    """Refresh the current song"""
    def __refreshCurrentSong(self):
        self.logger.debug("refreshCurrentSong()")
        cli = self.getClient()
        current_song = {}
        if cli:
            current_song = cli.playlistid(self.status.get('songid', ''))[0]
            cli.disconnect()
        if current_song != self.current_song:
            self.currentsong = current_song
            wx.PostEvent(self.window, MpdCurrentSongEvent(self.currentsong))
    
    #"""Pause playing the current song"""
    #def pause(self):
    #    self.logger.debug("pause()")
    #    cli = self.getClient()
    #    cli.pause()
    #    cli.disconnect()
    #"""Play the current song in queue"""
    #def play(self):
    #    self.logger.debug("play()")
    #    cli = self.getClient()
    #    if cli:
    #        cli.play()
    #        cli.disconnect()
    #"""Play the queue position"""
    #def playqueuepos(self, queue_pos):
    #    self.logger.debug("playqueuepos()")
    #    cli = self.getClient()
    #    if cli:
    #        cli.play(queue_pos)
    #        cli.disconnect()
    #""""""
    #def next(self):
    #    cli = self.getClient()
    #    if cli:
    #        cli.next()
    #        cli.disconnect()
    #""""""
    #def prev(self):
    #    cli = self.getClient()
    #    if cli:
    #        cli.previous()
    #        cli.disconnect()
    #""""""
    #def SetVolume(self, volume):
    #    self.logger.debug("OnVolChanged()")
    #    cli = self.getClient()
    #    if cli:
    #        cli.setvol(volume)
    #        cli.disconnect()

class MpdCmdFrame(wx.Frame):

    """"""
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.logger = logging.getLogger("MPDCMD")

        self.logger.info("Starting MPDCMD")

        # init client
        self.client = None

        # init mpd
        self.mpd = MpdThread(self)
        EVT_MPD_STATS(self, self.OnStatsChanged)
        EVT_MPD_STATUS(self, self.OnStatusChanged)
        EVT_MPD_CURRENTSONG(self, self.OnCurrentSongChanged)

        # init properties
        self.stats = {}
        self.status = {}
        self.current_song = {}

        # create interface
        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        nb = self.makeNotebook()
        self.main_sizer.Add(nb, 1, wx.EXPAND|wx.ALL, 1)
        
        self.currentSongText = wx.StaticText(self.main_panel, label="Not Playing")
        self.main_sizer.Add(self.currentSongText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)
        
        self.currentSongTime = wx.StaticText(self.main_panel, label="00:00/00:00")
        self.main_sizer.Add(self.currentSongTime, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)
        
        tr = self.makeTransport()
        self.main_sizer.Add(tr, 0, wx.EXPAND|wx.ALL, 5)

        self.main_panel.SetSizer(self.main_sizer)

        self.makeMenuBar()
        self.CreateStatusBar()

        self.logger.info("Initialising UI")

        # populate interface TODO: this blocks the ui on startup if connection fails
        #self.populateQueue()
        #self.populateAlbums()

        self.logger.info("Starting thread")

        self.mpd.start()

    """Convert seconds to time"""
    def secondsToTime(self, seconds: float) -> str:
        return "%02d:%02d" % (seconds//60, seconds%60)

    """MPD stats changed"""
    def OnStatsChanged(self, stats):
        self.stats = stats
        self.logger.info("Stats changed %s" % self.stats)
        self.updateTitle()
    """MPD status changed"""
    def OnStatusChanged(self, event):
        self.status = event.data
        self.logger.info("Status changed %s" % self.status)
        self.updatePlayPause()
        self.updateVolume()
        self.updateSongTime()
        self.mpd.refreshCurrentSong()
    """MPD current song changed"""
    def OnCurrentSongChanged(self, event):
        self.current_song = event.data
        self.logger.info("Song changed %s" % self.current_song)
        self.updateCurrentSong()

    """Album item selected"""
    def OnAlbumSelect(self, event):
        album_name = self.albumCtrl.GetItem(self.albumCtrl.GetFirstSelected(), col=0).GetText()
        self.logger.info("Album selected %s" % album_name)
        cli = self.getClient()
        if cli:
            cli.clear()
            cli.findadd('(Album == "%s")' % album_name)
            cli.disconnect()
        self.populateQueue()
        self.play()
    """Queue item selected"""
    def OnQueueSelect(self, event):
        queue_pos = int(self.queueCtrl.GetItem(self.queueCtrl.GetFirstSelected(), col=2).GetText())
        self.logger.info("Queue item selected %s", queue_pos)
        self.playqueuepos(queue_pos)

    """Update the title text"""
    def updateTitle(self):
        self.Title = "MPDCMD [Artists %s Albums %s Songs %s]" % (self.stats.get('artists', '?'), self.stats.get('albums', '?'), self.stats.get('songs', '?'))
    """"""
    def updatePlayPause(self):
        if self.status.get('state', '') == 'play':
            self.playButton.SetLabel("Pause")
        else:
            self.playButton.SetLabel("Play")
    """Update the volume value"""
    def updateVolume(self):
        self.currentVol.SetValue(int(self.status.get('volume', '0')))
    """Update song time"""
    def updateSongTime(self):
        elapsed = self.secondsToTime(float(self.status.get('elapsed', '0')))
        duration = self.secondsToTime(float(self.status.get('duration', '0')))
        self.currentSongTime.SetLabel("%s/%s" % (elapsed, duration))
    """Update current song"""
    def updateCurrentSong(self):
        for s in range(0, self.queueCtrl.GetItemCount()):
            pos = self.queueCtrl.GetItem(s, col=2).GetText()
            if self.current_song.get('pos', '') == str(pos):
                self.queueCtrl.SetItem(s, 0, '>')
            else:
                self.queueCtrl.SetItem(s, 0, ' ')
        wx.adv.NotificationMessage("MPDCMD", "%s. %s - %s\r\n%s" % (self.current_song.get('track', '?'), self.current_song.get('artist', '?'), self.current_song.get('title', '?'), self.current_song.get('album', '?'))).Show(5)
        self.currentSongText.SetLabel("%s. %s - %s (%s)" % (self.current_song.get('track', '?'), self.current_song.get('artist', '?'), self.current_song.get('title', '?'), self.current_song.get('album', '?')))
        self.SetStatusText("%s %s" % (self.current_song.get('file', '?'), self.current_song.get('format', '?')))

    """Make the notebook"""
    def makeNotebook(self):
        notebook = wx.Notebook(self.main_panel)

        self.queueCtrl = wx.ListCtrl(notebook)
        self.queueCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.queueCtrl.InsertColumn(0, "", width=20)
        self.queueCtrl.InsertColumn(1, "Id", width=50)
        self.queueCtrl.InsertColumn(2, "Position", width=70)
        self.queueCtrl.InsertColumn(3, "Album", width=150)
        self.queueCtrl.InsertColumn(4, "Artist", width=100)
        self.queueCtrl.InsertColumn(5, "Track", width=50)
        self.queueCtrl.InsertColumn(6, "Title", width=200)
        self.queueCtrl.SetColumnsOrder([0,1,2,3,4,5,6])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnQueueSelect, self.queueCtrl)
        notebook.AddPage(self.queueCtrl, "Queue")

        self.albumCtrl = wx.ListCtrl(notebook)
        self.albumCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.albumCtrl.InsertColumn(0, "Album", width=150)
        self.albumCtrl.InsertColumn(1, "Artist", width=100)
        self.albumCtrl.InsertColumn(2, "Tracks", width=50)
        self.albumCtrl.SetColumnsOrder([0,1,2])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAlbumSelect, self.albumCtrl)
        notebook.AddPage(self.albumCtrl, "Albums")

        return notebook
    """Make the transport"""
    def makeTransport(self):
        transport = wx.Panel(self.main_panel)
        tr_hori = wx.BoxSizer(wx.HORIZONTAL)

        prevButton = wx.Button(transport, label="Prev")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, prevButton)
        tr_hori.Add(prevButton, 0, wx.EXPAND|wx.ALL, 1)

        self.playButton = wx.Button(transport, label="")
        self.Bind(wx.EVT_BUTTON, self.OnPlay, self.playButton)
        tr_hori.Add(self.playButton, 0, wx.EXPAND|wx.ALL, 1)

        nextButton = wx.Button(transport, label="Next")
        self.Bind(wx.EVT_BUTTON, self.OnNext, nextButton)
        tr_hori.Add(nextButton, 0, wx.EXPAND|wx.ALL, 1)

        self.currentVol = wx.Slider(transport, minValue=0, maxValue=100, style=wx.SL_VALUE_LABEL)
        self.Bind(wx.EVT_SCROLL_CHANGED, self.OnVolChanged, self.currentVol)
        tr_hori.Add(self.currentVol, 0, wx.EXPAND|wx.ALL, 1)

        transport.SetSizer(tr_hori)
        return transport
    """Make the menu bar"""
    def makeMenuBar(self):
        fileMenu = wx.Menu()
        prefItem = fileMenu.Append(-1, "&Preferences", "Configure preferences")
        fileMenu.AppendSeparator()
        exitItem = fileMenu.Append(wx.ID_EXIT)
        
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnPref, prefItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    """Populate the queue list control"""
    def populateQueue(self):
        self.logger.debug("populateQueue()")
        cli = self.getClient()
        playlist_result = []
        if cli:
            playlist_result = cli.playlistid()
            cli.disconnect()
        self.queueCtrl.DeleteAllItems()
        for song in playlist_result:
            self.queueCtrl.Append(['',song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])
    """Populate the albums list control"""
    def populateAlbums(self):
        self.logger.debug("populateAlbums()")
        cli = self.getClient()
        albums = []
        if cli:
            albums_result = cli.list('AlbumSort')
            for album in albums_result:
                tracks = cli.find('(Album == "%s")' % album)
                is_various = False
                for t in range(1, len(tracks)):
                    if tracks[t-1]['artist'] != tracks[t]['artist']:
                        is_various = True
                        break
                albums.append([album, 'VA' if is_various else tracks[0]['artist'], len(tracks)])
            cli.disconnect()
        for album in albums:
            self.albumCtrl.Append(album)

    """Volume slider changed"""
    def OnVolChanged(self, event):
        vol = self.currentVol.GetValue()
        self.mpd.SetVolume(int(vol))
    """Play/pause clicked"""
    def OnPlay(self, event):
        self.logger.debug("OnPlay()")
        if self.status.get('state', '') == 'play':
            self.mpd.pause()
        else:
            self.mpd.play()
    """Next clicked"""
    def OnNext(self, event):
        self.logger.debug("OnNext()")
        self.mpd.next()
    """Previous clicked"""
    def OnPrev(self, event):
        self.logger.debug("OnPrev()")
        self.mpd.prev()

    """Preferences menu selected"""
    def OnPref(self, event):
        self.logger.debug("OnPref()")
        wx.MessageBox("TODO: show preferences window with ip and port options")
    """About menu selected"""
    def OnAbout(self, event):
        self.logger.debug("OnAbout()")
        wx.MessageBox("Some text", "Title", wx.OK|wx.ICON_INFORMATION)
    """Exit menu selected"""
    def OnExit(self, event):
        self.logger.debug("OnExit()")
        self.Close(True)
    """On window/frame close"""
    def OnClose(self, event):
        if self.mpd:
            self.mpd.stop()
        self.Destroy()

def main():
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    icon = wx.Icon()
    icon.LoadFile(".\\mpdcmd\\icons\\icon.png", type=wx.BITMAP_TYPE_PNG)
    frame.SetIcon(icon)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()