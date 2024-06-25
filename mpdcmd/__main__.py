import musicpd
import time
import wx
from threading import *

EVT_SONG_STATUS_ID = wx.Window.NewControlId()

def EVT_SONG_STATUS(win, func):
    win.Connect(-1, -1, EVT_SONG_STATUS_ID, func)

class SongStatusEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SONG_STATUS_ID)
        self.data = data

class SongStatusWorker(Thread):
    def __init__(self, notify_window, client):
        Thread.__init__(self)
        self._notify_window = notify_window
        self.client = client
        self._want_abort = 0
        self.start()
    def run(self):
        while not self._want_abort:
            status = self.client.status()
            wx.PostEvent(self._notify_window, SongStatusEvent(status))
            time.sleep(1)
    def abort(self):
        self._want_abort = 1

class MpdCmdFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MpdCmdFrame, self).__init__(*args, **kw)
        self.client = None
        self.current_songid = None
        self.current_playlist = None

        self.main_panel = wx.Panel(self)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        nb = self.makeNotebook()
        self.main_sizer.Add(nb, 1, wx.EXPAND|wx.ALL, 1)

        self.currentTrackText = wx.StaticText(self.main_panel, label="Not Playing")
        self.main_sizer.Add(self.currentTrackText, 0, wx.EXPAND|wx.ALL, 1)
        
        self.currentTrackTime = wx.StaticText(self.main_panel, label="0/0")
        self.main_sizer.Add(self.currentTrackTime, 0, wx.EXPAND|wx.ALL, 1)

        tr = self.makeTransport()
        self.main_sizer.Add(tr, 0, wx.EXPAND|wx.ALL, 1)

        self.main_panel.SetSizer(self.main_sizer)

        self.makeMenuBar()

        self.CreateStatusBar()

        self.populatePlaylist()
        self.populateAlbums()
        self.OnVolChanged(None)
        self.updateTitle()

        EVT_SONG_STATUS(self, self.OnSongStatus)
        self.worker = SongStatusWorker(self, self.getClient())

    def updateTitle(self):
        cli = self.getClient()
        stats = cli.stats()
        self.Title = "MPDCMD Artists %s Albums %s Songs %s" % (stats['artists'], stats['albums'], stats['songs'])
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
    def makeNotebook(self):
        notebook = wx.Notebook(self.main_panel)

        self.currentPlaylistCtrl = wx.ListCtrl(notebook)
        self.currentPlaylistCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.currentPlaylistCtrl.InsertColumn(0, "id")
        self.currentPlaylistCtrl.InsertColumn(1, "pos")
        self.currentPlaylistCtrl.InsertColumn(2, "Album")
        self.currentPlaylistCtrl.InsertColumn(3, "Artist")
        self.currentPlaylistCtrl.InsertColumn(4, "Track")
        self.currentPlaylistCtrl.InsertColumn(5, "Title")
        self.currentPlaylistCtrl.SetColumnsOrder([0,1,2,3,4,5])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnCurrentSelect, self.currentPlaylistCtrl)
        notebook.AddPage(self.currentPlaylistCtrl, "Current")

        self.albumCtrl = wx.ListCtrl(notebook)
        self.albumCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.albumCtrl.InsertColumn(0, "Album")
        self.albumCtrl.InsertColumn(1, "Artist")
        self.albumCtrl.InsertColumn(2, "Tracks")
        self.albumCtrl.SetColumnsOrder([0,1,2])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAlbumSelect, self.albumCtrl)
        notebook.AddPage(self.albumCtrl, "Albums")

        return notebook
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
    def secondsToTime(self, seconds: float):
        return "%d:%d" % (seconds//60, seconds%60)
    def populatePlaylist(self):
        cli = self.getClient()
        playlist = cli.playlistid()
        self.currentPlaylistCtrl.DeleteAllItems()
        for song in playlist:
            self.currentPlaylistCtrl.Append([song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])
    def populateTrack(self, status):
        cli = self.getClient()
        current_song = cli.playlistid(status['songid'])[0]
        self.currentTrackText.SetLabel("%s. %s - %s (%s)" % ( current_song['track'], current_song['artist'], current_song['title'], current_song['album']))
        self.SetStatusText("%s %s" % (current_song['file'], current_song['format']))
    def populateTime(self, status):
        elapsed = 0
        if 'elapsed' in status.keys():
            elapsed = self.secondsToTime(float(status['elapsed']))
        duration = 0
        if 'duration' in status.keys():
            duration = self.secondsToTime(float(status['duration']))
        self.currentTrackTime.SetLabel("%s/%s" % (elapsed, duration))
    def populateAlbums(self):
        cli = self.getClient()
        albums = cli.list('AlbumSort')
        for album in albums:
            tracks = cli.find('(Album == "%s")' % album)
            self.albumCtrl.Append([album, tracks[0]['artist'], len(tracks)])
    def OnSongStatus(self, event):
        self.populateTime(event.data)
        if 'songid' not in event.data.keys() or 'playlist' not in event.data.keys():
            return
        if event.data['songid'] == self.current_songid and event.data['playlist'] == self.current_playlist:
            return
        self.current_songid = event.data['songid']
        self.current_playlist = event.data['playlist']
        self.populateTrack(event.data)
    def OnVolChanged(self, event):
        cli = self.getClient()
        if event != None:
            vol = event.GetInt()
            cli.setvol(vol)
        else:
            vol = int(cli.getvol()['volume'])
        self.currentVol.SetValue(vol)
    def OnExit(self, event):
        if self.client != None:
            self.client.disconnect()
        if self.worker != None:
            self.worker.abort()
        self.Close(True)
    def OnPref(self, event):
        wx.MessageBox("TODO: show preferences window with ip and port options")
    def OnAbout(self, event):
        wx.MessageBox("Some text", "Title", wx.OK|wx.ICON_INFORMATION)
    def OnPrev(self, event):
        cli = self.getClient()
        cli.previous()
    def OnPlay(self, event):
        cli = self.getClient()
        status = cli.status()
        if status['state'] == "play":
            cli.pause()
        else:
            cli.play()
    def OnNext(self, event):
        cli = self.getClient()
        cli.next()
    def OnAlbumSelect(self, event):
        album_name = self.albumCtrl.GetItem(self.albumCtrl.GetFirstSelected(), col=0).GetText()
        cli = self.getClient()
        cli.clear()
        cli.findadd('(Album == "%s")' % album_name)
        cli.play()
        self.populatePlaylist()
    def OnCurrentSelect(self, event):
        cli = self.getClient()
        cli.play(int(self.currentPlaylistCtrl.GetItem(self.currentPlaylistCtrl.GetFirstSelected(), col=1).GetText()))
    def getClient(self):
        if self.client == None:
            self.client = musicpd.MPDClient()
            self.client.connect('192.168.1.10', '6600')
        return self.client

def main():
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()