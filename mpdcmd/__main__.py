import logging
import musicpd
import os
import threading
import time
import wx
import wx.adv
from threading import *

logging.basicConfig(level=logging.WARN)

mcEVT_MPD_CONNECTION = wx.NewEventType()
EVT_MPD_CONNECTION = wx.PyEventBinder(mcEVT_MPD_CONNECTION, 1)
class MpdConnectionEvent(wx.PyCommandEvent):
    def __init__(self, value: str):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CONNECTION, -1)
        self._value = value
    def GetValue(self) -> str:
        return self._value

mcEVT_MPD_STATS = wx.NewEventType()
EVT_MPD_STATS = wx.PyEventBinder(mcEVT_MPD_STATS, 1)
class MpdStatsEvent(wx.PyCommandEvent):
    def __init__(self, value: dict):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_STATS, -1)
        self._value = value
    def GetValue(self) -> dict:
        return self._value

mcEVT_MPD_STATUS = wx.NewEventType()
EVT_MPD_STATUS = wx.PyEventBinder(mcEVT_MPD_STATUS, 1)
class MpdStatusEvent(wx.PyCommandEvent):
    def __init__(self, value: dict):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_STATUS, -1)
        self._value = value
    def GetValue(self) -> dict:
        return self._value

mcEVT_MPD_CURRENTSONG = wx.NewEventType()
EVT_MPD_CURRENTSONG = wx.PyEventBinder(mcEVT_MPD_CURRENTSONG, 1)
class MpdCurrentSongEvent(wx.PyCommandEvent):
    def __init__(self, value: dict):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CURRENTSONG, -1)
        self._value = value
    def GetValue(self) -> dict:
        return self._value

mcEVT_MPD_QUEUE = wx.NewEventType()
EVT_MPD_QUEUE = wx.PyEventBinder(mcEVT_MPD_QUEUE, 1)
class MpdQueueEvent(wx.PyCommandEvent):
    def __init__(self, value: list):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_QUEUE, -1)
        self._value = value
    def GetValue(self) -> list:
        return self._value

mcEVT_MPD_ALBUMS = wx.NewEventType()
EVT_MPD_ALBUMS = wx.PyEventBinder(mcEVT_MPD_ALBUMS, 1)
class MpdAlbumsEvent(wx.PyCommandEvent):
    def __init__(self, value: list):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_ALBUMS, -1)
        self._value = value
    def GetValue(self) -> list:
        return self._value

class MpdConnection():

    """"""
    def __init__(self, window: wx.Window, host: str, port: str):
        self.window = window
        self.host = host
        self.port = port
        
        self.logger = logging.getLogger("MpdConnection")
        self.logger.info("Starting MpdConnection")

        self.connection_status = None

    """Get a connected client"""
    def getClient(self) -> musicpd.MPDClient:
        musicpd.CONNECTION_TIMEOUT = 1
        self.logger.debug("Connecting to %s:%s", self.host, self.port)
        client = musicpd.MPDClient()
        try:
            client.connect(self.host, self.port)
            connection_status = "Connected"
        except musicpd.MPDError as e:
            client = False
            connection_status = "Connection error"
            self.logger.warning(connection_status)
        if self.connection_status != connection_status:
            self.connection_status = connection_status
            wx.PostEvent(self.window, MpdConnectionEvent(connection_status))
        return client

class MpdController():

    """"""
    def __init__(self, window: wx.Window, host: str, port: str):
        self.window = window
        self.host = host
        self.port = port
        
        self.logger = logging.getLogger("MpdController")
        self.logger.info("Starting MpdController")

        self.connection = MpdConnection(self.window, host, port)

        self.stats = {}
        self.current_song = {}

        self.status_thread = None

    """"""
    def start(self) -> None:
        self.logger.info("Starting thread")
        self.status_thread = MpdStatusThread(self.window, self.connection)
        self.status_thread.start()
        pass

    """"""
    def stop(self) -> None:
        self.logger.info("Stopping thread")
        if self.status_thread:
            self.status_thread.stop()

    """Refresh the stats"""
    def refreshStats(self) -> None:
        Thread(target=self.__refreshStats).start()
    def __refreshStats(self) -> None:
        self.logger.debug("refreshStats()")
        cli = self.connection.getClient()
        stats = {}
        if cli:
            stats = cli.stats()
            cli.disconnect()
        if self.stats != stats:
            self.stats = stats
            wx.PostEvent(self.window, MpdStatsEvent(self.stats))

    """Refresh the current song"""
    def refreshCurrentSong(self) -> None:
        Thread(target=self.__refreshCurrentSong).start()
    def __refreshCurrentSong(self) -> None:
        self.logger.debug("refreshCurrentSong()")
        cli = self.connection.getClient()
        current_song = {}
        if cli:
            current_song = cli.playlistid(self.status_thread.status.get('songid', ''))[0]
            cli.disconnect()
        if self.current_song != current_song:
            self.current_song = current_song
            wx.PostEvent(self.window, MpdCurrentSongEvent(self.current_song))

    """Refresh albums"""
    def refreshAlbums(self):
        Thread(target=self.__refreshAlbums).start()
    def __refreshAlbums(self):
        self.logger.debug("refreshAlbums()")
        cli = self.connection.getClient()
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

    """Refresh the queue"""
    def refreshQueue(self):
        Thread(target=self.__refreshQueue).start()
    def __refreshQueue(self):
        self.logger.debug("refreshQueue()")
        cli = self.connection.getClient()
        queue = {}
        if cli:
            queue = cli.playlistid()
            cli.disconnect()
            wx.PostEvent(self.window, MpdQueueEvent(queue))

    """Play the queue position"""
    def playQueuePos(self, queue_pos):
        self.logger.debug("playQueuePos()")
        Thread(target=self.__playQueuePos, args=(queue_pos,)).start()
    def __playQueuePos(self, queue_pos):
        cli = self.connection.getClient()
        if cli:
            cli.play(queue_pos)
            cli.disconnect()

    """Play the album tag"""
    def playAlbumTag(self, album_name: str) -> None:
        Thread(target=self.__playAlbumTag, args=(album_name,)).start()
    def __playAlbumTag(self, album_name: str) -> None:
        cli = self.connection.getClient()
        if cli:
            cli.clear()
            cli.findadd('(Album == "%s")' % album_name)
            queue = cli.playlistid()
            cli.play()
            cli.disconnect()
            wx.PostEvent(self.window, MpdQueueEvent(queue))

    """Pause playing the current song"""
    def pause(self):
        self.logger.debug("pause()")
        Thread(target=self.__pause).start()
    def __pause(self):
        cli = self.connection.getClient()
        if cli:
            cli.pause()
            cli.disconnect()

    """Play the current song in queue"""
    def play(self):
        self.logger.debug("play()")
        Thread(target=self.__play).start()
    def __play(self):
        cli = self.connection.getClient()
        if cli:
            cli.play()
            cli.disconnect()

    """Next song in queue"""
    def next(self):
        self.logger.debug("next()")
        Thread(target=self.__next).start()
    def __next(self):
        cli = self.connection.getClient()
        if cli:
            cli.next()
            cli.disconnect()

    """Previous song in qeueue"""
    def prev(self):
        self.logger.debug("prev()")
        Thread(target=self.__prev).start()
    def __prev(self):
        cli = self.connection.getClient()
        if cli:
            cli.previous()
            cli.disconnect()

    """Set volume"""
    def setVolume(self, volume):
        self.logger.debug("setVolume()")
        Thread(target=self.__setVolume, args=(volume,)).start()
    def __setVolume(self, volume):
        cli = self.connection.getClient()
        if cli:
            cli.setvol(volume)
            cli.disconnect()

class MpdStatusThread(threading.Thread):

    """"""
    def __init__(self, parent: wx.Window, connection: MpdConnection):
        threading.Thread.__init__(self)
        self.parent = parent
        self.connection = connection
        
        self.logger = logging.getLogger("MpdThread")

        self.logger.info("Starting MpdThread")

        self.status = {}

        self.running = False

    """Start the thread (override)"""
    def run(self):
        self.running = True
        while self.running:
            self.logger.debug("tick()")
            self.__refreshStatus()
            time.sleep(1)
    """Stop the thread"""
    def stop(self) -> None:
        self.running = False

    """Refresh the status info"""
    def __refreshStatus(self) -> None:
        self.logger.debug("refreshStatus()")
        cli = self.connection.getClient()
        status = {}
        if cli:
            status = cli.status()
            cli.disconnect()
        if self.status != status:
            self.status = status
            wx.PostEvent(self.parent, MpdStatusEvent(self.status))

class MpdCmdFrame(wx.Frame):

    """"""
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.logger = logging.getLogger("MpdCmdFrame")
        self.logger.info("Starting MpdCmdFrame")

        # init mpd
        self.mpd = MpdController(self, "192.168.1.10", "6600") # TODO: load from config
        self.Bind(EVT_MPD_CONNECTION, self.OnConnectionChanged)
        self.Bind(EVT_MPD_STATS, self.OnStatsChanged)
        self.Bind(EVT_MPD_STATUS, self.OnStatusChanged)
        self.Bind(EVT_MPD_CURRENTSONG, self.OnCurrentSongChanged)
        self.Bind(EVT_MPD_ALBUMS, self.OnAlbumsChanged)
        self.Bind(EVT_MPD_QUEUE, self.OnQueueChanged)

        # init properties
        self.stats = {}
        self.status = {}
        self.current_song = {}
        self.connection_status = "Not connected"
        self.volume_changing = False

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

        self.logger.info("Initialising UI")

        self.makeMenuBar()
        self.CreateStatusBar()

        self.updateStatus()
        self.updateStatusBarText()

        self.mpd.start()

        self.logger.info("Refreshing MPD data")

        self.mpd.refreshStats()
        self.mpd.refreshAlbums()
        self.mpd.refreshQueue()

    """Make the notebook"""
    def makeNotebook(self) -> wx.Notebook:
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
        try:
            self.queueCtrl.SetColumnsOrder([0,1,2,3,4,5,6])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnQueueSelect, self.queueCtrl)
        notebook.AddPage(self.queueCtrl, "Queue")

        self.albumCtrl = wx.ListCtrl(notebook)
        self.albumCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.albumCtrl.InsertColumn(0, "Album", width=150)
        self.albumCtrl.InsertColumn(1, "Artist", width=100)
        self.albumCtrl.InsertColumn(2, "Tracks", width=50)
        try:
            self.albumCtrl.SetColumnsOrder([0,1,2])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAlbumSelect, self.albumCtrl)
        notebook.AddPage(self.albumCtrl, "Albums")

        return notebook
    """Make the transport"""
    def makeTransport(self) -> wx.Panel:
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
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.OnVolChangeStart, self.currentVol)
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBRELEASE, self.OnVolChangeEnd, self.currentVol)
        tr_hori.Add(self.currentVol, 0, wx.EXPAND|wx.ALL, 1)

        transport.SetSizer(tr_hori)
        return transport
    """Make the menu bar"""
    def makeMenuBar(self) -> None:
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

    """Convert seconds to time"""
    def secondsToTime(self, seconds: float) -> str:
        return "%02d:%02d" % (seconds//60, seconds%60)

    """MPD connection changed"""
    def OnConnectionChanged(self, event: MpdConnectionEvent) -> None:
        self.connection_status = event.GetValue()
        self.logger.info("Connection changed %s" % self.connection_status)
        self.updateStatusBarText()
    """MPD stats changed"""
    def OnStatsChanged(self, event: MpdStatsEvent) -> None:
        self.stats = event.GetValue()
        self.logger.info("Stats changed %s" % self.stats)
        self.updateTitle()
    """MPD status changed"""
    def OnStatusChanged(self, event: MpdStatusEvent) -> None:
        self.status = event.GetValue()
        self.logger.info("Status changed %s" % self.status)
        self.updateStatus()
        self.mpd.refreshCurrentSong()
    """MPD current song changed"""
    def OnCurrentSongChanged(self, event: MpdCurrentSongEvent) -> None:
        self.current_song = event.GetValue()
        self.logger.info("Song changed %s" % self.current_song)
        self.updateCurrentSong()
    """Albums changed"""
    def OnAlbumsChanged(self, event: MpdAlbumsEvent) -> None:
        albums = event.GetValue()
        self.logger.info("Albums changed %d" % len(albums))
        for album in albums:
            self.albumCtrl.Append(album)
    """Queue changed"""
    def OnQueueChanged(self, event: MpdQueueEvent) -> None:
        queue = event.GetValue()
        self.logger.info("Queue changed %s" % queue)
        self.queueCtrl.DeleteAllItems()
        for song in queue:
            self.queueCtrl.Append(['',song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])

    """Album item selected"""
    def OnAlbumSelect(self, event: wx.ListEvent) -> None:
        album_name = self.albumCtrl.GetItem(self.albumCtrl.GetFirstSelected(), col=0).GetText()
        self.logger.info("Album selected %s" % album_name)
        self.mpd.playAlbumTag(album_name)
    """Queue item selected"""
    def OnQueueSelect(self, event: wx.ListEvent) -> None:
        queue_pos = int(self.queueCtrl.GetItem(self.queueCtrl.GetFirstSelected(), col=2).GetText())
        self.logger.info("Queue item selected %s", queue_pos)
        self.mpd.playQueuePos(queue_pos)

    """Update the title text"""
    def updateTitle(self) -> None:
        self.Title = "MPDCMD [Artists %s Albums %s Songs %s]" % (self.stats.get('artists', '?'), self.stats.get('albums', '?'), self.stats.get('songs', '?'))
    """Update status related ui"""
    def updateStatus(self) -> None:
        self.updatePlayPause()
        self.updateVolume()
        self.updateSongTime()
    """Update play/pause button"""
    def updatePlayPause(self) -> None:
        if self.status.get('state', '') != 'play':
            self.playButton.SetLabel("Play")
        else:
            self.playButton.SetLabel("Pause")
    """Update the volume value"""
    def updateVolume(self) -> None:
        if self.volume_changing == False:
            self.currentVol.SetValue(int(self.status.get('volume', '0')))
    """Update song time"""
    def updateSongTime(self) -> None:
        elapsed = self.secondsToTime(float(self.status.get('elapsed', '0')))
        duration = self.secondsToTime(float(self.status.get('duration', '0')))
        self.currentSongTime.SetLabel("%s/%s" % (elapsed, duration))
    """Update current song"""
    def updateCurrentSong(self) -> None:
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
    def updateStatusBarText(self) -> None:
        self.SetStatusText("%s %s | %s:%s %s" % (self.current_song.get('file', 'FILE'), self.current_song.get('format', 'FORMAT'), self.mpd.host, self.mpd.port, self.connection_status))

    """Play/pause clicked"""
    def OnPlay(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnPlay()")
        if self.status.get('state', '') != 'play':
            self.mpd.play()
        else:
            self.mpd.pause()
    """Next clicked"""
    def OnNext(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnNext()")
        self.mpd.next()
    """Previous clicked"""
    def OnPrev(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnPrev()")
        self.mpd.prev()
    """Volume slider changed"""
    def OnVolChanged(self, event: wx.CommandEvent) -> None:
        vol = self.currentVol.GetValue()
        self.mpd.setVolume(int(vol))
    def OnVolChangeStart(self, event) -> None:
        self.volume_changing = True
    def OnVolChangeEnd(self, event) -> None:
        self.volume_changing = False

    """Preferences menu selected"""
    def OnPref(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnPref()")
        wx.MessageBox("TODO: show preferences window with ip and port options")
    """About menu selected"""
    def OnAbout(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnAbout()")
        wx.MessageBox("Some text", "Title", wx.OK|wx.ICON_INFORMATION)
    """Exit menu selected"""
    def OnExit(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnExit()")
        self.Close(True)
    """On window/frame close"""
    def OnClose(self, event: wx.CommandEvent) -> None:
        if self.mpd:
            self.mpd.stop()
        self.Destroy()

def main():
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    icon = wx.Icon()
    icon.LoadFile(os.path.join(os.path.curdir, 'mpdcmd', 'icons', 'icon.png'), type=wx.BITMAP_TYPE_PNG)
    frame.SetIcon(icon)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()