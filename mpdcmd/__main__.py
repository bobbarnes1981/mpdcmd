import musicpd
import wx

class MpdCmdFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MpdCmdFrame, self).__init__(*args, **kw)

        panel = wx.Panel(self)

        notebook = wx.Notebook(panel, size=(640,480)) # TODO

        self.currentPlaylistPanel = wx.Panel(notebook)
        self.currentPlaylistCtrl = wx.ListCtrl(self.currentPlaylistPanel, size=(600,400))
        self.currentPlaylistCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.currentPlaylistCtrl.InsertColumn(0, "id")
        self.currentPlaylistCtrl.InsertColumn(1, "pos")
        self.currentPlaylistCtrl.InsertColumn(2, "Album")
        self.currentPlaylistCtrl.InsertColumn(3, "Artist")
        self.currentPlaylistCtrl.InsertColumn(4, "Track")
        self.currentPlaylistCtrl.InsertColumn(5, "Title")
        self.currentPlaylistCtrl.SetColumnsOrder([0,1,2,3,4,5])
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnCurrentSelect, self.currentPlaylistCtrl)
        notebook.AddPage(self.currentPlaylistPanel, "Current")

        self.albumsPanel = wx.Panel(notebook)
        self.albumCtrl = wx.ListCtrl(self.albumsPanel, size=(600,400))
        self.albumCtrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.albumCtrl.InsertColumn(0, "Album")
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAlbumSelect, self.albumCtrl)
        notebook.AddPage(self.albumsPanel, "Albums")

        self.currentTrackText = wx.StaticText(panel, label="")

        self.currentVolText = wx.StaticText(panel, label="0")

        prevButton = wx.Button(panel, label="Prev")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, prevButton)
        
        playButton = wx.Button(panel, label="Play/Pause")
        self.Bind(wx.EVT_BUTTON, self.OnPlay, playButton)
        
        nextButton = wx.Button(panel, label="Next")
        self.Bind(wx.EVT_BUTTON, self.OnNext, nextButton)
        
        volUpButton = wx.Button(panel, label="+")
        self.Bind(wx.EVT_BUTTON, self.OnVolUp, volUpButton)
        
        volDnButton = wx.Button(panel, label="-")
        self.Bind(wx.EVT_BUTTON, self.OnVolDn, volDnButton)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(notebook, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))

        sizer.Add(self.currentTrackText, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        sizer.Add(prevButton, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        sizer.Add(playButton, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        sizer.Add(nextButton, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        sizer.Add(volUpButton, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        sizer.Add(self.currentVolText, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        sizer.Add(volDnButton, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))

        panel.SetSizer(sizer)

        self.makeMenuBar()

        self.CreateStatusBar()
        self.SetStatusText("some status bar text")

        self.populatePlaylist()
        self.adjVolume(0)
        self.populateTrack()
        self.populateAlbums()
    def makeMenuBar(self):
        fileMenu = wx.Menu()
        helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
                                    "This is a help menu item")
        fileMenu.AppendSeparator()
        exitItem = fileMenu.Append(wx.ID_EXIT)
        
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
    def populatePlaylist(self):
        cli = self.getClient()
        playlist = cli.playlistid()
        for song in playlist:
            self.currentPlaylistCtrl.Append([song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])
        cli.disconnect()
    def populateTrack(self):
        cli = self.getClient()
        status = cli.status()
        current_song = cli.playlistid(status['songid'])[0]
        self.currentTrackText.SetLabel("%s, %s, %s, %s, %s, %s, %s, %s" % (current_song['file'], current_song['format'], current_song['artist'], current_song['album'], current_song['title'], current_song['track'], current_song['duration'], current_song['pos']))
        cli.disconnect()
    def populateAlbums(self):
        cli = self.getClient()
        albums = cli.list('AlbumSort')
        for album in albums:
            self.albumCtrl.Append([album])
        cli.disconnect()
    def adjVolume(self, adj):
        cli = self.getClient()
        vol = int(cli.getvol()['volume'])
        if adj != 0:
            vol = vol + adj
            cli.setvol(vol)
        self.currentVolText.SetLabel(str(vol))
        cli.disconnect()
    def OnExit(self, event):
        self.Close(True)
    def OnHello(self, event):
        wx.MessageBox("Hello messagebox")
    def OnAbout(self, event):
        wx.MessageBox("Some text",
                      "Title",
                      wx.OK|wx.ICON_INFORMATION)
    def OnPrev(self, event):
        cli = self.getClient()
        cli.previous()
        cli.disconnect()
        self.populateTrack()
    def OnPlay(self, event):
        cli = self.getClient()
        status = cli.status()
        if status['state'] == "play":
            cli.pause()
        else:
            cli.play()
        cli.disconnect()
        self.populateTrack()
    def OnNext(self, event):
        cli = self.getClient()
        cli.next()
        cli.disconnect()
        self.populateTrack()
    def OnVolUp(self, event):
        self.adjVolume(+5)
    def OnVolDn(self, event):
        self.adjVolume(-5)
    def OnAlbumSelect(self, event):

        album_name = self.albumCtrl.GetItem(self.albumCtrl.GetFirstSelected(), col=0).GetText()
        # clear queue, add all to queue, play

        cli = self.getClient()
        tracks = cli.find("(Album == '%s')" % album_name)
        print(tracks)
        cli.disconnect()

    def OnCurrentSelect(self, event):
        cli = self.getClient()
        cli.play(int(self.currentPlaylistCtrl.GetItem(self.currentPlaylistCtrl.GetFirstSelected(), col=1).GetText()))
        cli.disconnect()
        self.populateTrack()
    def getClient(self):
        cli = musicpd.MPDClient()
        cli.connect('192.168.1.10', '6600')
        return cli

def main():
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    frame.Show()
    app.MainLoop()

    #stats = cli.stats()
    #print('Artists %s' % stats['artists'])
    #print('Albums %s' % stats['albums'])
    #print('Songs %s' % stats['songs'])

    #status = cli.status()
    #print('volume %s' % status['volume'])
    #print('playlist %s' % status['playlist'])
    #print('playlistlength %s' % status['playlistlength'])
    #print('state %s' % status['state'])
    #print('song %s' % status['song'])
    #print('songid %s' % status['songid'])
    #if 'nextsong' in status.keys():
    #    print('nextsong %s' % status['nextsong'])
    #    print('nextsongid %s' % status['nextsongid'])
    #print('elapsed %s' % status['elapsed'])
    #print('duration %s' % status['duration'])

    #playlists = cli.listplaylists()
    #print(playlists)

    #all = cli.listall()
    #print(all)

    #cli.disconnect()

if __name__ == '__main__':
    main()