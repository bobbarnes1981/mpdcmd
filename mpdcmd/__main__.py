import logging
import musicpd
import threading
import time
import wx
import wx.adv
from threading import *

logging.basicConfig(level=logging.INFO)

#https://wiki.wxpython.org/Non-Blocking%20Gui

EVT_MPD_CONNECTION_ID = wx.NewIdRef()
def EVT_MPD_CONNECTION(win, func):
    win.Connect(-1, -1, EVT_MPD_CONNECTION_ID, func)
class MpdConnectionEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_CONNECTION_ID)
        self.data = data

EVT_MPD_STATS_ID = wx.NewIdRef()
def EVT_MPD_STATS(win, func):
    win.Connect(-1, -1, EVT_MPD_STATS_ID, func)
class MpdStatsEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_STATS_ID)
        self.data = data

EVT_MPD_STATUS_ID = wx.NewIdRef()
def EVT_MPD_STATUS(win, func):
    win.Connect(-1, -1, EVT_MPD_STATUS_ID, func)
class MpdStatusEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_STATUS_ID)
        self.data = data

EVT_MPD_CURRENTSONG_ID = wx.NewIdRef()
def EVT_MPD_CURRENTSONG(win, func):
    win.Connect(-1, -1, EVT_MPD_CURRENTSONG_ID, func)
class MpdCurrentSongEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_CURRENTSONG_ID)
        self.data = data

EVT_MPD_QUEUE_ID = wx.NewIdRef()
def EVT_MPD_QUEUE(win, func):
    win.Connect(-1, -1, EVT_MPD_QUEUE_ID, func)
class MpdQueueEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_QUEUE_ID)
        self.data = data

EVT_MPD_ALBUMS_ID = wx.NewIdRef()
def EVT_MPD_ALBUMS(win, func):
    win.Connect(-1, -1, EVT_MPD_ALBUMS_ID, func)
class MpdAlbumsEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_MPD_ALBUMS_ID)
        self.data = data

class MpdController():

    """"""
    def __init__(self, window, host, port):
        self.window = window
        self.host = host
        self.port = port
        
        self.logger = logging.getLogger("MpdController")

        self.logger.info("Starting MpdController")

        self.stats = {}
        self.currentsong = {}
        self.connection_status = None

    def start(self):
        self.thread = MpdThread(self.window, self.host, self.port)
        self.thread.start()

    def stop(self):
        if self.thread:
            self.thread.stop()

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
    """Refresh the queue"""
    def __refreshQueue(self):
        self.logger.debug("refreshQueue()")
        cli = self.getClient()
        queue = []
        if cli:
            queue = cli.playlistid()
            cli.disconnect()
            wx.PostEvent(self.window, MpdQueueEvent(queue))
    """Refresh albums"""
    def __refreshAlbums(self):
        self.logger.debug("refreshAlbums()")
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
            wx.PostEvent(self.window, MpdAlbumsEvent(albums))

    """Pause playing the current song"""
    def __pause(self):
        cli = self.getClient()
        if cli:
            cli.pause()
            cli.disconnect()
    """Pause playing the current song"""
    def pause(self):
        self.logger.debug("pause()")
        Thread(target=self.__pause).start()
    """Play the current song in queue"""
    def __play(self):
        cli = self.getClient()
        if cli:
            cli.play()
            cli.disconnect()
    """Play the current song in queue"""
    def play(self):
        self.logger.debug("play()")
        Thread(target=self.__play).start()
    """Play the queue position"""
    def __playQueuePos(self, queue_pos):
        cli = self.getClient()
        if cli:
            cli.play(queue_pos)
            cli.disconnect()
    """Play the queue position"""
    def playQueuePos(self, queue_pos):
        self.logger.debug("playQueuePos()")
        Thread(target=self.__playQueuePos).start()
    """Next song in queue"""
    def __next(self):
        cli = self.getClient()
        if cli:
            cli.next()
            cli.disconnect()
    """Next song in queue"""
    def next(self):
        self.logger.debug("next()")
        Thread(target=self.__next).start()
    """Previous song in queue"""
    def __prev(self):
        cli = self.getClient()
        if cli:
            cli.previous()
            cli.disconnect()
    """Previous song in qeueue"""
    def prev(self):
        self.logger.debug("prev()")
        Thread(target=self.__prev).start()
    """Set volume"""
    def __setVolume(self, volume):
        cli = self.getClient()
        if cli:
            cli.setvol(volume)
            cli.disconnect()
    """Set volume"""
    def setVolume(self, volume):
        self.logger.debug("setVolume()")
        Thread(target=self.__setVolume, args=(volume,)).start()

class MpdThread(threading.Thread):

    """"""
    def __init__(self, window, host, port):
        threading.Thread.__init__(self)
        self.window = window
        self.host= host
        self.port = port
        
        self.logger = logging.getLogger("MpdThread")

        self.logger.info("Starting MpdThread")

        self.status = {}

        self.running = False

    """Get a connected client"""
    def getClient(self) -> musicpd.MPDClient:
        musicpd.CONNECTION_TIMEOUT = 1
        self.logger.debug("Connecting to %s:%s", self.host, self.port)
        client = musicpd.MPDClient()
        try:
            client.connect(self.host, self.port)
        except musicpd.MPDError as e:
            client = False
            connection_status = "Connection error"
            self.logger.warning(connection_status)
            if self.connection_status != connection_status:
                self.connection_status = connection_status
                wx.PostEvent(self.window, MpdConnectionEvent(connection_status))
        return client
    
    """Stop the thread"""
    def stop(self):
        self.running = False
    """Start the thread (override)"""
    def run(self):
        self.running = True
        while self.running:
            self.logger.debug("tick()")
            self.__refreshStatus()
            time.sleep(1)

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

class MpdCmdFrame(wx.Frame):

    """"""
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.logger = logging.getLogger("MpdCmdFrame")

        self.logger.info("Starting MpdCmdFrame")

        # init client
        self.client = None

        # init mpd
        self.mpd = MpdController(self, "192.168.1.10", "6600") # TODO: load from config
        EVT_MPD_CONNECTION(self, self.OnConnectionChanged)
        EVT_MPD_STATS(self, self.OnStatsChanged)
        EVT_MPD_STATUS(self, self.OnStatusChanged)
        EVT_MPD_CURRENTSONG(self, self.OnCurrentSongChanged)
        EVT_MPD_QUEUE(self, self.OnQueueChanged)
        EVT_MPD_ALBUMS(self, self.OnAlbumsChanged)

        # init properties
        self.stats = {}
        self.status = {}
        self.current_song = {}
        self.connection_status = "Not connected"

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

        self.updateStatus()
        self.updateStatusBarText()

        self.logger.info("Starting thread")

        self.mpd.start()

    """Convert seconds to time"""
    def secondsToTime(self, seconds: float) -> str:
        return "%02d:%02d" % (seconds//60, seconds%60)

    """MPD connection changed"""
    def OnConnectionChanged(self, event):
        self.connection_status = event.data
        self.logger.info("Connection changed %s" % self.connection_status)
        self.updateStatusBarText()
    """MPD stats changed"""
    def OnStatsChanged(self, event):
        self.stats = event.data
        self.logger.info("Stats changed %s" % self.stats)
        self.updateTitle()
    """MPD status changed"""
    def OnStatusChanged(self, event):
        self.status = event.data
        self.logger.info("Status changed %s" % self.status)
        self.updateStatus()
        self.mpd.refreshCurrentSong()
    """MPD current song changed"""
    def OnCurrentSongChanged(self, event):
        self.current_song = event.data
        self.logger.info("Song changed %s" % self.current_song)
        self.updateCurrentSong()
    """Queue changed"""
    def OnQueueChanged(self, event):
        queue = event.data
        self.logger.info("Queue changed %s" % queue)
        self.queueCtrl.DeleteAllItems()
        for song in queue:
            self.queueCtrl.Append(['',song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])
    """Albums changed"""
    def OnAlbumsChanged(self, event):
        # TODO
        for album in albums:
            self.albumCtrl.Append(album)

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
    """Update status related ui"""
    def updateStatus(self):
        self.updatePlayPause()
        self.updateVolume()
        self.updateSongTime()
    """Update play/pause button"""
    def updatePlayPause(self):
        if self.status.get('state', '') != 'play':
            self.playButton.SetLabel("Play")
        else:
            self.playButton.SetLabel("Pause")
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
        self.updateStatusBarText()
    """Update status bar text"""
    def updateStatusBarText(self):
        self.SetStatusText("%s %s | %s:%s %s" % (self.current_song.get('file', 'FILE'), self.current_song.get('format', 'FORMAT'), self.mpd.host, self.mpd.port, self.connection_status))

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

    """Volume slider changed"""
    def OnVolChanged(self, event):
        vol = self.currentVol.GetValue()
        self.mpd.SetVolume(int(vol))
    """Play/pause clicked"""
    def OnPlay(self, event):
        self.logger.debug("OnPlay()")
        if self.status.get('state', '') != 'play':
            self.mpd.play()
        else:
            self.mpd.pause()
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