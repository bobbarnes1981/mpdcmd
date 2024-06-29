import json
import logging
import musicpd
import os
import threading
import wx
import wx.adv

logging.basicConfig(level=logging.WARN,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_icon(file):
    icon = wx.Icon()
    icon.LoadFile(os.path.join(os.path.curdir, 'mpdcmd', 'icons', "%s.png" % file), type=wx.BITMAP_TYPE_PNG)
    return icon

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

mcEVT_MPD_SONGS = wx.NewEventType()
EVT_MPD_SONGS = wx.PyEventBinder(mcEVT_MPD_SONGS, 1)
class MpdSongsEvent(wx.PyCommandEvent):
    def __init__(self, value: list):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_SONGS, -1)
        self._value = value
    def GetValue(self) -> list:
        return self._value

mcEVT_MPD_PLAYLISTS = wx.NewEventType()
EVT_MPD_PLAYLISTS = wx.PyEventBinder(mcEVT_MPD_PLAYLISTS, 1)
class MpdPlaylistsEvent(wx.PyCommandEvent):
    def __init__(self, value: list):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_PLAYLISTS, -1)
        self._value = value
    def GetValue(self) -> list:
        return self._value

mcEVT_MPD_ALBUMART = wx.NewEventType()
EVT_MPD_ALBUMART = wx.PyEventBinder(mcEVT_MPD_ALBUMART, 1)
class MpdAlbumArtEvent(wx.PyCommandEvent):
    def __init__(self, value):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_ALBUMART, -1)
        self._value = value
    def GetValue(self):
        return self._value

mcEVT_MPD_CTRL_CURRENTSONG = wx.NewEventType()
EVT_MPD_CTRL_CURRENTSONG = wx.PyEventBinder(mcEVT_MPD_CTRL_CURRENTSONG, 1)
class MpdCurrentSongEvent(wx.PyCommandEvent):
    def __init__(self, value: dict):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CTRL_CURRENTSONG, -1)
        self._value = value
    def GetValue(self) -> dict:
        return self._value

mcEVT_MPD_CTRL_QUEUE = wx.NewEventType()
EVT_MPD_CTRL_QUEUE = wx.PyEventBinder(mcEVT_MPD_CTRL_QUEUE, 1)
class MpdQueueEvent(wx.PyCommandEvent):
    def __init__(self, value: list):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CTRL_QUEUE, -1)
        self._value = value
    def GetValue(self) -> list:
        return self._value

mcEVT_MPD_CTRL_ALBUMS = wx.NewEventType()
EVT_MPD_CTRL_ALBUMS = wx.PyEventBinder(mcEVT_MPD_CTRL_ALBUMS, 1)
class MpdAlbumsEvent(wx.PyCommandEvent):
    def __init__(self, value: list):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CTRL_ALBUMS, -1)
        self._value = value
    def GetValue(self) -> list:
        return self._value

mcEVT_MPD_IDLE_PLAYER = wx.NewEventType()
EVT_MPD_IDLE_PLAYER = wx.PyEventBinder(mcEVT_MPD_IDLE_PLAYER, 1)
class MpdIdlePlayerEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_PLAYER, -1)

mcEVT_MPD_IDLE_MIXER = wx.NewEventType()
EVT_MPD_IDLE_MIXER = wx.PyEventBinder(mcEVT_MPD_IDLE_MIXER, 1)
class MpdIdleMixerEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_MIXER, -1)

mcEVT_MPD_IDLE_PLAYLIST = wx.NewEventType()
EVT_MPD_IDLE_PLAYLIST = wx.PyEventBinder(mcEVT_MPD_IDLE_PLAYLIST, 1)
class MpdIdlePlaylistEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_PLAYLIST, -1)

mcEVT_MPD_IDLE_UPDATE = wx.NewEventType()
EVT_MPD_IDLE_UPDATE = wx.PyEventBinder(mcEVT_MPD_IDLE_UPDATE, 1)
class MpdIdleUpdateEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_UPDATE, -1)

mcEVT_MPD_IDLE_DATABASE = wx.NewEventType()
EVT_MPD_IDLE_DATABASE = wx.PyEventBinder(mcEVT_MPD_IDLE_DATABASE, 1)
class MpdIdleDatabaseEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_DATABASE, -1)

"""Handles executing requests to MPD"""
class MpdConnection():

    """Initialise the MpdConnection"""
    def __init__(self, window: wx.Window, host: str, port: str, username: str, password: str):
        self.window = window
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        if not self.host:
            self.host = '127.0.0.1'
        if not self.port:
            self.port = '6600'

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s" % type(self).__name__)

        self.connection_status = None

    """Execute the provided function with a connected client"""
    def execute(self, func: callable, *args):
        musicpd.CONNECTION_TIMEOUT = 1
        os.environ['MPD_HOST'] = self.host
        os.environ['MPD_PORT'] = self.port
        os.environ['MPD_USERNAME'] = self.username
        os.environ['MPD_PASSWORD'] = self.password
        try:
            self.logger.debug("Connecting to %s:%s", self.host, self.port)
            with musicpd.MPDClient() as client:
                connection_status = "Connected"
                self.logger.debug(connection_status)
                func(client, *args)
        except musicpd.MPDError as e:
            connection_status = "Connection error"
            self.logger.warning("Connection error %s" % func.__name__)
            self.logger.warning(e)
        if self.connection_status != connection_status:
            self.connection_status = connection_status
            wx.PostEvent(self.window, MpdConnectionEvent(connection_status))

"""Provides interface to MPD"""
class MpdController():

    """Initialise the MpdController"""
    def __init__(self, window: wx.Window, host: str, port: str, username: str, password:str):
        self.window = window
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s" % type(self).__name__)

        self.connection = MpdConnection(self.window, host, port, username, password)

        self.stats = {}
        self.status = {}
        self.current_song = {}

        self.idle_thread = None

    """Start the background threads"""
    def start(self) -> None:
        self.logger.info("Starting thread")
        self.idle_thread = MpdIdleThread(self.window, self.connection)
        self.idle_thread.start()

    """Stop the status background thread"""
    def stop(self) -> None:
        self.logger.info("Stopping thread")
        if self.idle_thread:
            self.idle_thread.stop()

    """Refresh the stats"""
    def refreshStats(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshStats,)).start()
    def __refreshStats(self, cli) -> None:
        self.logger.debug("refreshStats()")
        stats = {}
        stats = cli.stats()
        if self.stats != stats:
            self.stats = stats
            wx.PostEvent(self.window, MpdStatsEvent(self.stats))

    """Refresh the status info"""
    def refreshStatus(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshStatus,)).start()
    def __refreshStatus(self, cli) -> None:
        self.logger.debug("refreshStatus()")
        status = {}
        status = cli.status()
        if self.status != status:
            self.status = status
            wx.PostEvent(self.window, MpdStatusEvent(self.status))

    """Refresh the current song"""
    def refreshCurrentSong(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshCurrentSong,)).start()
    def __refreshCurrentSong(self, cli) -> None:
        self.logger.debug("refreshCurrentSong()")
        songid = self.status.get('songid', None)
        self.logger.debug("songid '%s'" % songid)
        if songid:
            current_song = {}
            current_song = cli.playlistid(int(songid))[0]
            if self.current_song != current_song:
                self.current_song = current_song
                wx.PostEvent(self.window, MpdCurrentSongEvent(self.current_song))

    """Refresh albums"""
    def refreshAlbums(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshAlbums,)).start()
    def __refreshAlbums(self, cli) -> None:
        self.logger.debug("refreshAlbums()")
        albums = []
        albums_result = cli.list('AlbumSort')
        for album in albums_result:
            tracks = cli.find('(Album == "%s")' % album)
            is_various = False
            for t in range(1, len(tracks)):
                if tracks[t-1]['artist'] != tracks[t]['artist']:
                    is_various = True
                    break
            albums.append([album, 'VA' if is_various else tracks[0]['artist'], len(tracks)])
        wx.PostEvent(self.window, MpdAlbumsEvent(albums))

    """Refresh the queue"""
    def refreshQueue(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshQueue,)).start()
    def __refreshQueue(self, cli) -> None:
        self.logger.debug("refreshQueue()")
        queue = {}
        queue = cli.playlistid()
        wx.PostEvent(self.window, MpdQueueEvent(queue))

    """"""
    def refreshSongs(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshSongs,)).start()
    def __refreshSongs(self, cli) -> None:
        self.logger.debug("refreshSongs()")
        songs = {}
        songs = cli.listall()
        wx.PostEvent(self.window, MpdSongsEvent(songs))

    """"""
    def refreshPlaylists(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshPlaylists,)).start()
    def __refreshPlaylists(self, cli) -> None:
        self.logger.debug("refreshPlaylists()")
        playlists = {}
        playlists = cli.listplaylists()
        wx.PostEvent(self.window, MpdPlaylistsEvent(playlists))
    
    """"""
    def refreshAlbumArt(self, songid, file) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__refreshAlbumArt, songid, file)).start()
    def __refreshAlbumArt(self, cli, songid, file) -> None:
        self.logger.debug("refreshAlbumArt()")
        album_art = {}
        offset = 0
        album_art = {'size':'1','binary':'','data':b''}
        data = b''
        while offset < int(album_art['size']):
            album_art = cli.albumart(file, offset)
            offset += int(album_art['binary'])
            data += album_art['data']
        self.__saveAlbumArt(songid, data)
        wx.PostEvent(self.window, MpdAlbumArtEvent(songid))

    """Play the queue position"""
    def playQueuePos(self, queue_pos) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__playQueuePos, queue_pos)).start()
    def __playQueuePos(self, cli, queue_pos) -> None:
        self.logger.debug("playQueuePos()")
        cli.play(queue_pos)

    """Play the album tag"""
    def playAlbumTag(self, album_name: str) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__playAlbumTag, album_name)).start()
    def __playAlbumTag(self, cli, album_name: str) -> None:
        self.logger.debug("playAlbumTag()")
        cli.clear()
        cli.findadd('(Album == "%s")' % album_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue))

    """Pause playing the current song"""
    def pause(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__pause,)).start()
    def __pause(self, cli) -> None:
        self.logger.debug("pause()")
        cli.pause()

    """Play the current song in queue"""
    def play(self):
        threading.Thread(target=self.connection.execute, args=(self.__play,)).start()
    def __play(self, cli) -> None:
        self.logger.debug("play()")
        cli.play()

    """Next song in queue"""
    def next(self):
        threading.Thread(target=self.connection.execute, args=(self.__next,)).start()
    def __next(self, cli) -> None:
        self.logger.debug("next()")
        cli.next()

    """Previous song in qeueue"""
    def prev(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__prev,)).start()
    def __prev(self, cli) -> None:
        self.logger.debug("prev()")
        cli.previous()

    """Set volume"""
    def setVolume(self, volume) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__setVolume, volume)).start()
    def __setVolume(self, cli, volume) -> None:
        self.logger.debug("setVolume()")
        cli.setvol(volume)

    """Update"""
    def update(self) -> None:
        threading.Thread(target=self.connection.execute, args=(self.__update,)).start()
    def __update(self, cli):
        self.logger.debug("update()")
        cli.update()
    
    """"""
    def __saveAlbumArt(self, songid, data):
        ext, typ = self.__getFileExtension(data)
        orig_path = self.__getArtPath('albumart', songid, ext)
        with open(orig_path, 'wb') as f:
            f.write(data)
        if typ != wx.BITMAP_TYPE_PNG:
            orig_img = wx.Image(orig_path, type=typ)
            new_path = self.__getArtPath('albumart', songid, 'png')
            orig_img.SaveFile(new_path, wx.BITMAP_TYPE_PNG)
            os.remove(orig_path)

    """"""
    def __getFileExtension(self, data: str) -> None:
        if data.startswith(bytes.fromhex('ffd8ffe0')):
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('89504e47')):
            return ('png', wx.BITMAP_TYPE_PNG)
        raise Exception('Unhandled file type %s' % data[:5])

    """"""
    def __getArtPath(self, folder, songid, ext) -> str:
        return os.path.join(os.path.curdir, 'mpdcmd', folder, "%s.%s" % (songid, ext))

    """"""
    def getDefaultAlbumArt(self) -> wx.Bitmap:
        path = self.__getArtPath('icons', 'icon', 'png')
        return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()
    
    """"""
    def getAlbumArt(self, songid) -> wx.Bitmap:
        path = self.__getArtPath('albumart', songid, 'png')
        if os.path.isfile(path):
            return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()
        return self.getDefaultAlbumArt()

""""""
class MpdIdleThread(threading.Thread):

    """Initialise the MpdIdleThread"""
    def __init__(self, parent: wx.Window, connection: MpdConnection):
        threading.Thread.__init__(self)
        self.parent = parent
        self.connection = connection
        
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s" % type(self).__name__)

        self.actions = {
            'player': self.__actionPlayer,
            'mixer': self.__actionMixer,
            'playlist': self.__actionPlaylist,
            'update': self.__actionUpdate,
            'database': self.__actionDatabase,
        }
        self.running = False
        self.socket_timeout = 10

    """Start the thread (override)"""
    def run(self):
        self.running = True
        while self.running:
            self.logger.debug("tick()")
            self.connection.execute(self.__idle)
    """Stop the thread"""
    def stop(self) -> None:
        self.running = False

    """Refresh the status info"""
    def __idle(self, cli) -> None:
        self.logger.debug("idle()")
        cli.socket_timeout = self.socket_timeout
        try:
            self.logger.debug('Starting idle')
            idles = cli.idle()
            self.logger.debug('Idle response %s' % idles)
            for idle in idles:
                if idle in self.actions.keys():
                    self.actions[idle]()
                else:
                    self.logger.warning('Unhandled idle response %s' % idle)
        except TimeoutError:
            self.logger.debug('Idle timeout after %ds' % self.socket_timeout)

    """"""
    def __actionPlayer(self):
        # start/stop/seek or changed tags of current song
        self.logger.debug('Player action')
        wx.PostEvent(self.parent, MpdIdlePlayerEvent())

    """"""
    def __actionMixer(self):
        # volume has been changed
        self.logger.debug('Mixer action')
        wx.PostEvent(self.parent, MpdIdleMixerEvent())

    """"""
    def __actionPlaylist(self):
        # queue has been modified
        self.logger.debug('Playlist action')
        wx.PostEvent(self.parent, MpdIdlePlaylistEvent())

    """"""
    def __actionUpdate(self):
        # update has started or finished
        self.logger.debug('Update action')
        wx.PostEvent(self.parent, MpdIdleUpdateEvent())

    """"""
    def __actionDatabase(self):
        # database was modified
        self.logger.debug('Database action')
        wx.PostEvent(self.parent, MpdIdleDatabaseEvent())

"""Mpd main window"""
class MpdCmdFrame(wx.Frame):

    """Initialise MpdCmdFrame"""
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s" % type(self).__name__)

        self.preferences_file = os.path.join(os.path.curdir, 'preferences.json')
        self.preferences = self.loadPreferences()

        # init mpd
        self.mpd = MpdController(self, self.preferences.get('host', ''), self.preferences.get('port', ''), self.preferences.get('username', ''), self.preferences.get('password', ''))

        self.Bind(EVT_MPD_CONNECTION, self.OnConnectionChanged)
        self.Bind(EVT_MPD_STATS, self.OnStatsChanged)
        self.Bind(EVT_MPD_STATUS, self.OnStatusChanged)
        self.Bind(EVT_MPD_SONGS, self.OnSongsChanged)
        self.Bind(EVT_MPD_PLAYLISTS, self.OnPlaylistsChanged)
        self.Bind(EVT_MPD_ALBUMART, self.OnAlbumArtChanged)
        
        self.Bind(EVT_MPD_CTRL_CURRENTSONG, self.OnCurrentSongChanged)
        self.Bind(EVT_MPD_CTRL_ALBUMS, self.OnAlbumsChanged)
        self.Bind(EVT_MPD_CTRL_QUEUE, self.OnQueueChanged)

        self.Bind(EVT_MPD_IDLE_PLAYER, self.OnIdlePlayer)
        self.Bind(EVT_MPD_IDLE_MIXER, self.OnIdleMixer)
        self.Bind(EVT_MPD_IDLE_PLAYLIST, self.OnIdlePlaylist)
        self.Bind(EVT_MPD_IDLE_UPDATE, self.OnIdleUpdate)
        self.Bind(EVT_MPD_IDLE_DATABASE, self.OnIdleDatabase)

        # init properties
        self.stats = {}
        self.status = {}
        self.current_song = {}
        self.connection_status = "Not connected"
        self.volume_changing = False

        self.timer = wx.Timer(self)
        self.elapsed = 0
        self.duration = 0
        self.Bind(wx.EVT_TIMER, self.OnTick, self.timer)
        self.playing = False

        # create layout
        self.main_panel = wx.Panel(self)
        #self.main_panel.SetBackgroundColour((0xff, 0x00, 0x00))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        self.top_panel = wx.Panel(self.main_panel)
        #self.top_panel.SetBackgroundColour((0x00, 0xff, 0x00))
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_panel.SetSizer(self.top_sizer)
        self.main_sizer.Add(self.top_panel, 1, wx.EXPAND|wx.ALL, 1)

        self.bot_panel = wx.Panel(self.main_panel)
        #self.bot_panel.SetBackgroundColour((0x00, 0x00, 0xff))
        self.bot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bot_panel.SetSizer(self.bot_sizer)
        self.main_sizer.Add(self.bot_panel, 0, wx.EXPAND|wx.ALL, 1)

        self.l_panel = wx.Panel(self.bot_panel)
        #self.l_panel.SetBackgroundColour((0xff, 0xff, 0x00))
        self.l_sizer = wx.BoxSizer(wx.VERTICAL)
        self.l_panel.SetSizer(self.l_sizer)
        self.bot_sizer.Add(self.l_panel, 1, wx.EXPAND|wx.ALL, 1)
        
        self.r_panel = wx.Panel(self.bot_panel)
        #self.r_panel.SetBackgroundColour((0x00, 0xff, 0xff))
        self.r_sizer = wx.BoxSizer(wx.VERTICAL)
        self.r_panel.SetSizer(self.r_sizer)
        self.bot_sizer.Add(self.r_panel, 0, wx.EXPAND|wx.ALL, 1)

        # create ui
        nb = self.makeNotebook(self.top_panel)
        self.top_sizer.Add(nb, 1, wx.EXPAND|wx.ALL, 1)

        self.currentSongText = wx.StaticText(self.l_panel, label="Not Playing")
        self.l_sizer.Add(self.currentSongText, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)
        
        self.currentSongTime = wx.StaticText(self.l_panel, label="00:00/00:00")
        self.l_sizer.Add(self.currentSongTime, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)
        
        tr = self.makeTransport(self.l_panel)
        self.l_sizer.Add(tr, 0, wx.ALL|wx.ALL, 1)

        bitmap = self.mpd.getDefaultAlbumArt()
        self.art = wx.StaticBitmap(self.r_panel, wx.ID_ANY, bitmap, size=(80,80)) # TODO: better solution to keep art square?
        self.r_sizer.Add(self.art, 0, wx.EXPAND|wx.ALL, 1)

        self.logger.info("Initialising UI")

        self.makeMenuBar()
        self.CreateStatusBar()

        self.updateStatus()
        self.updateStatusBarText()
        self.updateCurrentSongTimeText()

        self.mpd.start()
        self.timer.Start(1000, wx.TIMER_CONTINUOUS)

        self.logger.info("Refreshing MPD data")

        self.mpd.refreshStats()
        self.mpd.refreshStatus()
        self.mpd.refreshAlbums()
        self.mpd.refreshQueue()

    """Load preferences"""
    def loadPreferences(self):
        if os.path.isfile(self.preferences_file) == False:
            with open(self.preferences_file, 'w') as file:
                preferences = {"host":"","port":"","username":"","password":""}
                file.write(json.dumps(preferences))
        with open(self.preferences_file, 'r') as f:
            return json.loads(f.read())

    """Make the notebook"""
    def makeNotebook(self, parent) -> wx.Notebook:
        notebook = wx.Notebook(parent)

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
    def makeTransport(self, parent) -> wx.Panel:
        transport = wx.Panel(parent)
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
        
        serverMenu = wx.Menu()
        updateItem = serverMenu.Append(-1, "&Update", "Trigger a server update")

        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(serverMenu, "&Server")
        menuBar.Append(helpMenu, "&Help")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnMenuPref, prefItem)
        self.Bind(wx.EVT_MENU, self.OnMenuExit, exitItem)
        self.Bind(wx.EVT_MENU, self.OnMenuUpdate, updateItem)
        self.Bind(wx.EVT_MENU, self.OnMenuAbout, aboutItem)

    """Convert seconds to time"""
    def secondsToTime(self, seconds: float) -> str:
        return "%02d:%02d" % (seconds//60, seconds%60)

    """On timer tick"""
    def OnTick(self, event: wx.TimerEvent) -> None:
        self.logger.debug("OnTick")
        if self.playing:
            self.elapsed += 1
        self.updateCurrentSongTimeText()

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
    """MPD songs changed"""
    def OnSongsChanged(self, event: MpdSongsEvent) -> None:
        songs = event.GetValue()
        self.logger.info("Songs changed %s" % songs)
        # TODO: update songs list
    """MPD playlists changed"""
    def OnPlaylistsChanged(self, event: MpdPlaylistsEvent) -> None:
        playlists = event.GetValue()
        self.logger.info("Playlists changed %s" % playlists)
        # TODO: update playlists list
    """MPD albumart changed"""
    def OnAlbumArtChanged(self, event: MpdAlbumArtEvent) -> None:
        songid = event.GetValue()
        self.logger.info("Albumart changed %s" % songid)
        bitmap = self.mpd.getAlbumArt(self.current_song.get('id', ''))
        self.art.Bitmap = bitmap

    """MPD current song changed"""
    def OnCurrentSongChanged(self, event: MpdCurrentSongEvent) -> None:
        self.current_song = event.GetValue()
        self.logger.info("Song changed %s" % self.current_song)
        self.mpd.refreshAlbumArt(self.current_song.get('id', ''), self.current_song.get('file', ''))
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
        self.logger.info("Queue changed %s" % len(queue))
        self.queueCtrl.DeleteAllItems()
        for song in queue:
            self.queueCtrl.Append(['',song['id'],song['pos'],song['album'],song['artist'],song['track'],song['title']])

    """Idle player event"""
    def OnIdlePlayer(self, event: MpdIdlePlayerEvent) -> None:
        self.logger.debug("Idle player")
        self.mpd.refreshStatus()
    """Idle mixer event"""
    def OnIdleMixer(self, event: MpdIdleMixerEvent) -> None:
        self.logger.debug("Idle mixer")
        self.mpd.refreshStatus()
    """Idle playlist event"""
    def OnIdlePlaylist(self, event: MpdIdlePlaylistEvent) -> None:
        self.logger.debug("Idle playlist")
        self.mpd.refreshQueue()
    """Idle update event"""
    def OnIdleUpdate(self, event: MpdIdleUpdateEvent) -> None:
        self.logger.debug("Idle update")
    """Idle database event"""
    def OnIdleDatabase(self, event: MpdIdleDatabaseEvent) -> None:
        self.logger.debug("Idle database")
        # TODO: refresh albums and songs?

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
    """Update play/pause button label"""
    def updatePlayPause(self) -> None:
        if self.status.get('state', '') != 'play':
            self.playButton.SetLabel("Play")
            self.playing = False
        else:
            self.playButton.SetLabel("Pause")
            self.playing = True
    """Update the volume slider value"""
    def updateVolume(self) -> None:
        if self.volume_changing == False:
            self.currentVol.SetValue(int(self.status.get('volume', '0')))
    """Update song time"""
    def updateSongTime(self) -> None:
        self.elapsed = float(self.status.get('elapsed', '0'))
        self.duration = float(self.status.get('duration', '0'))
        self.updateCurrentSongTimeText()
    """Update current song"""
    def updateCurrentSong(self) -> None:
        for s in range(0, self.queueCtrl.GetItemCount()):
            pos = self.queueCtrl.GetItem(s, col=2).GetText()
            if self.current_song.get('pos', '') == str(pos):
                self.queueCtrl.SetItem(s, 0, '>')
            else:
                self.queueCtrl.SetItem(s, 0, ' ')
        notification = wx.adv.NotificationMessage("MPDCMD", "%s. %s - %s\r\n%s" % (self.current_song.get('track', '?'), self.current_song.get('artist', '?'), self.current_song.get('title', '?'), self.current_song.get('album', '?')))
        notification.SetIcon(wx.Icon(self.mpd.getAlbumArt(self.current_song.get('id', ''))))
        notification.Show(5)
        self.currentSongText.SetLabel("%s. %s - %s (%s)" % (self.current_song.get('track', '?'), self.current_song.get('artist', '?'), self.current_song.get('title', '?'), self.current_song.get('album', '?')))
        self.updateStatusBarText()

    """Update status bar text"""
    def updateStatusBarText(self) -> None:
        self.SetStatusText("%s %s | %s:%s %s" % (self.current_song.get('file', 'FILE'), self.current_song.get('format', 'FORMAT'), self.mpd.host, self.mpd.port, self.connection_status))
    """Update current song time text"""
    def updateCurrentSongTimeText(self):
        elapsed = self.secondsToTime(self.elapsed)
        duration = self.secondsToTime(self.duration)
        self.currentSongTime.SetLabel("%s/%s" % (elapsed, duration))

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
    def OnMenuPref(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuPref()")
        preferences = MpdPreferencesFrame(self.preferences, self, title='Preferences', size=(320,270))
        preferences.Show()
    """About menu selected"""
    def OnMenuAbout(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuAbout()")
        wx.MessageBox("Music Player Daemon Command\r\nWxPython MPD Client", "About", wx.OK|wx.ICON_INFORMATION)
    """Update menu selected"""
    def OnMenuUpdate(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuUpdate()")
        self.mpd.update()
        wx.MessageBox("Update triggered", "Update", wx.OK|wx.ICON_INFORMATION)
    """Exit menu selected"""
    def OnMenuExit(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OMenuExit()")
        self.Close(True)
    """On window/frame close"""
    def OnClose(self, event: wx.CommandEvent) -> None:
        self.logger.debug("OnClose()")
        if self.mpd:
            self.mpd.stop()
        self.timer.Stop()
        self.Destroy()


"""Mpd main window"""
class MpdPreferencesFrame(wx.Frame):
    def __init__(self, preferences, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s" % type(self).__name__)

        self.preferences = preferences

        panel = wx.Panel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        hostLabel = wx.StaticText(panel, label='Host')
        sizer.Add(hostLabel, 0, wx.EXPAND|wx.ALL, 1)

        hostText = wx.TextCtrl(panel, value=self.preferences.get('host', ''))
        sizer.Add(hostText, 0, wx.EXPAND|wx.ALL, 1)

        portLabel = wx.StaticText(panel, label='Port')
        sizer.Add(portLabel, 0, wx.EXPAND|wx.ALL, 1)

        portText = wx.TextCtrl(panel, value=self.preferences.get('port', ''))
        sizer.Add(portText, 0, wx.EXPAND|wx.ALL, 1)

        usernameLabel = wx.StaticText(panel, label='Username')
        sizer.Add(usernameLabel, 0, wx.EXPAND|wx.ALL, 1)

        usernameText = wx.TextCtrl(panel, value=self.preferences.get('username', ''))
        sizer.Add(usernameText, 0, wx.EXPAND|wx.ALL, 1)

        passwordLabel = wx.StaticText(panel, label='Password')
        sizer.Add(passwordLabel, 0, wx.EXPAND|wx.ALL, 1)

        passwordText = wx.TextCtrl(panel, value=self.preferences.get('password', ''))
        sizer.Add(passwordText, 0, wx.EXPAND|wx.ALL, 1)

        cancelButton = wx.Button(panel, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancelButton)
        sizer.Add(cancelButton, 0, wx.EXPAND|wx.ALL, 1)

        saveButton = wx.Button(panel, label="Save")
        self.Bind(wx.EVT_BUTTON, self.OnSave, saveButton)
        sizer.Add(saveButton, 0, wx.EXPAND|wx.ALL, 1)

    """"""
    def OnSave(self, event: wx.PyCommandEvent) -> None:
        self.logger.debug("OnSave()")

    """"""
    def OnCancel(self, event: wx.PyCommandEvent) -> None:
        self.logger.debug("OnCancel()")

def main():
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    frame.SetIcon(get_icon('icon'))
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()