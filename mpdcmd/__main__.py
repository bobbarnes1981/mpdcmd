import logging
import musicpd
import wx
from threading import *

class MpdCmdFrame(wx.Frame):

    """"""
    def __init__(self, *args, **kw):
        super(MpdCmdFrame, self).__init__(*args, **kw)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("MPDCMD")

        # init client
        self.client = None

        # init timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.tick, self.timer)

        # init properties
        self.stats = None
        self.status = None
        self.current_song = None

        # create interface
        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        nb = self.makeNotebook()
        self.main_sizer.Add(nb, 1, wx.EXPAND|wx.ALL, 1)
        
        self.currentSongText = wx.StaticText(self.main_panel, label="Not Playing")
        self.main_sizer.Add(self.currentSongText, 0, wx.EXPAND|wx.ALL, 1)
        
        self.currentSongTime = wx.StaticText(self.main_panel, label="0/0")
        self.main_sizer.Add(self.currentSongTime, 0, wx.EXPAND|wx.ALL, 1)
        
        tr = self.makeTransport()
        self.main_sizer.Add(tr, 0, wx.EXPAND|wx.ALL, 1)

        self.main_panel.SetSizer(self.main_sizer)
        
        self.makeMenuBar()
        self.CreateStatusBar()

        # populate interface
        self.populateQueue()
        self.populateAlbums()

        # refresh
        self.refreshStats()
        self.refreshStatus()
                    
        self.timer.Start(1000)

    """Convert seconds to time"""
    def secondsToTime(self, seconds: float) -> str:
        return "%02d:%02d" % (seconds//60, seconds%60)
    """Get a connected client"""
    def getClient(self) -> musicpd.MPDClient:
        # TODO: load from config
        host = '192.168.1.10'
        port = '6600'
        self.logger.debug("Connecting to %s:%s", host, port)
        client = musicpd.MPDClient()
        client.connect(host, port)
        return client
    
    """Timer tick"""
    def tick(self, event):
        self.logger.debug("tick()")
        self.refreshStatus()

    """Refresh the stats"""
    def refreshStats(self):
        self.logger.debug("refreshStats()")
        cli = self.getClient()
        stats = cli.stats()
        cli.disconnect()
        if stats != self.stats:
            self.OnStatsChanged(stats)
    """Refresh the status info"""
    def refreshStatus(self):
        self.logger.debug("refreshStatus()")
        cli = self.getClient()
        status = cli.status()
        cli.disconnect()
        if status != self.status:
            self.OnStatusChanged(status)
    """Refresh the current song"""
    def refreshCurrentSong(self):
        self.logger.debug("refreshCurrentSong()")
        cli = self.getClient()
        current_song = cli.playlistid(self.status['songid'])[0]
        cli.disconnect()
        if current_song != self.current_song:
            self.OnCurrentSongChanged(current_song)

    """MPD stats changed"""
    def OnStatsChanged(self, stats):
        self.stats = stats
        self.logger.info("Stats changed %s" % self.stats)
        self.updateTitle()
    """MPD status changed"""
    def OnStatusChanged(self, status):
        self.status = status
        self.logger.info("Status changed %s" % self.status)
        self.current_elapsed = float(self.status['elapsed'])
        self.updateVolume()
        self.updateSongTime()
        self.refreshCurrentSong()
    """MPD current song changed"""
    def OnCurrentSongChanged(self, current_song):
        self.current_song = current_song
        self.logger.info("Song changed %s" % self.current_song)
        self.updateCurrentSong()
    """Album item selected"""
    def OnAlbumSelect(self, event):
        album_name = self.albumCtrl.GetItem(self.albumCtrl.GetFirstSelected(), col=0).GetText()
        self.logger.info("Album selected %s" % album_name)
        cli = self.getClient()
        cli.clear()
        cli.findadd('(Album == "%s")' % album_name)
        cli.disconnect()
        self.populateQueue()
        self.play()
        self.refreshStatus()
    """Queue item selected"""
    def OnQueueSelect(self, event):
        queue_pos = int(self.queueCtrl.GetItem(self.queueCtrl.GetFirstSelected(), col=2).GetText())
        self.logger.info("Queue item selected %s", queue_pos)
        cli = self.getClient()
        cli.play(queue_pos)
        cli.disconnect()

    """Update the title text"""
    def updateTitle(self):
        self.Title = "MPDCMD [Artists %s Albums %s Songs %s]" % (self.stats['artists'], self.stats['albums'], self.stats['songs'])
    """Update the volume value"""
    def updateVolume(self):
        self.currentVol.SetValue(int(self.status['volume']))
    """Update song time"""
    def updateSongTime(self):
        elapsed = 0
        if 'elapsed' in self.status.keys():
            elapsed = self.secondsToTime(float(self.status['elapsed']))
        duration = 0
        if 'duration' in self.status.keys():
            duration = self.secondsToTime(float(self.status['duration']))
        self.currentSongTime.SetLabel("%s/%s" % (elapsed, duration))
    """Update current song"""
    def updateCurrentSong(self):
        for s in range(0, self.queueCtrl.GetItemCount()):
            pos = self.queueCtrl.GetItem(s, col=2).GetText()
            if self.current_song['pos'] == str(pos):
                self.queueCtrl.SetItem(s, 0, '>')
            else:
                self.queueCtrl.SetItem(s, 0, ' ')
        self.currentSongText.SetLabel("%s. %s - %s (%s)" % (self.current_song['track'], self.current_song['artist'], self.current_song['title'], self.current_song['album']))
        self.SetStatusText("%s %s" % (self.current_song['file'], self.current_song['format']))

    """Make the notebook"""
    def makeNotebook(self):
        notebook = wx.Notebook(self.main_panel)

        self.queueCtrl = wx.ListCtrl(notebook)
        self.queueCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.queueCtrl.InsertColumn(0, "playing")
        self.queueCtrl.InsertColumn(1, "id")
        self.queueCtrl.InsertColumn(2, "pos")
        self.queueCtrl.InsertColumn(3, "Album")
        self.queueCtrl.InsertColumn(4, "Artist")
        self.queueCtrl.InsertColumn(5, "Track")
        self.queueCtrl.InsertColumn(6, "Title")
        self.queueCtrl.SetColumnsOrder([0,1,2,3,4,5,6])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnQueueSelect, self.queueCtrl)
        notebook.AddPage(self.queueCtrl, "Current")

        self.albumCtrl = wx.ListCtrl(notebook)
        self.albumCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.albumCtrl.InsertColumn(0, "Album")
        self.albumCtrl.InsertColumn(1, "Artist")
        self.albumCtrl.InsertColumn(2, "Tracks")
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

        playButton = wx.Button(transport, label="Play/Pause")
        self.Bind(wx.EVT_BUTTON, self.OnPlay, playButton)
        tr_hori.Add(playButton, 0, wx.EXPAND|wx.ALL, 1)

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
        playlist = cli.playlistid()
        cli.disconnect()
        self.queueCtrl.DeleteAllItems()
        for song in playlist:
            self.queueCtrl.Append(['',song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])
    """Populate the albums list control"""
    def populateAlbums(self):
        self.logger.debug("populateAlbums()")
        cli = self.getClient()
        albums = cli.list('AlbumSort')
        for album in albums:
            tracks = cli.find('(Album == "%s")' % album)
            self.albumCtrl.Append([album, tracks[0]['artist'], len(tracks)])
        cli.disconnect()

    """Play the current song in queue"""
    def play(self):
        self.logger.debug("play()")
        cli = self.getClient()
        cli.play()
        cli.disconnect()
    """Pause playing the current song"""
    def pause(self):
        self.logger.debug("pause()")
        cli = self.getClient()
        cli.pause()
        cli.disconnect()

    """Volume slider changed"""
    def OnVolChanged(self, event):
        self.logger.debug("OnVolChanged()")
        cli = self.getClient()
        vol = int(cli.getvol()['volume'])
        cli.disconnect()
        self.currentVol.SetValue(vol)
    """Previous clicked"""
    def OnPrev(self, event):
        self.logger.debug("OnPrev()")
        cli = self.getClient()
        cli.previous()
        cli.disconnect()
        self.refreshStatus()
    """Play/pause clicked"""
    def OnPlay(self, event):
        self.logger.debug("OnPlay()")
        self.refreshStatus()
        if self.status['state'] == "play":
            self.pause()
        else:
            self.play()
        self.refreshStatus()
    """Next clicked"""
    def OnNext(self, event):
        self.logger.debug("OnNext()")
        cli = self.getClient()
        cli.next()
        cli.disconnect()
        self.refreshStatus()

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