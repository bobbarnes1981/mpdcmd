import base64
import json
import logging
import os
import threading
import musicpd
import wx
import wx.adv

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_icon(file):
    icon = wx.Icon()
    icon.LoadFile(
        os.path.join(os.path.curdir, 'mpdcmd', 'icons', "%s.png" % file),
        type=wx.BITMAP_TYPE_PNG)
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
    def __init__(self, value: str):
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_ALBUMART, -1)
        self._value = value
    def GetValue(self) -> str:
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
        self.logger.info("Starting %s", type(self).__name__)

        self.connection_status = None

    """Execute the provided function with a connected client"""
    def execute(self, func: callable, *args):
        #musicpd.CONNECTION_TIMEOUT = 1
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
            self.logger.warning("Connection error %s", func.__name__)
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

        self.art_folder = 'albumart'

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.connection = MpdConnection(self.window, host, port, username, password)

        self.stats = {}
        self.status = {}
        self.queue = {}
        self.current_song = {}

        self.idle_thread = None

        self.__createArtFolder(self.art_folder)

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
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_stats,)).start()
    def __refresh_stats(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_stats()")
        stats = {}
        stats = cli.stats()
        if self.stats != stats:
            self.stats = stats
            wx.PostEvent(self.window, MpdStatsEvent(self.stats))

    """Refresh the status info"""
    def refreshStatus(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_status,)).start()
    def __refresh_status(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_status()")
        status = {}
        status = cli.status()
        if self.status != status:
            self.status = status
            wx.PostEvent(self.window, MpdStatusEvent(self.status))

    """Refresh the current song"""
    def refreshCurrentSong(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_current_song,)).start()
    def __refresh_current_song(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_current_song()")
        songid = self.status.get('songid', None)
        self.logger.debug("songid '%s'", songid)
        if songid:
            current_song = {}
            current_song = cli.playlistid(int(songid))[0]
            if self.current_song != current_song:
                self.current_song = current_song
                wx.PostEvent(self.window, MpdCurrentSongEvent(self.current_song))

    """Refresh albums"""
    def refreshAlbums(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_albums,)).start()
    def __refresh_albums(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_albums()")
        albums = []
        albums_result = cli.list('Album')
        for album in albums_result:
            tracks = cli.find('(Album == "%s")' % album)
            is_various = False
            duration = 0
            for t in range(1, len(tracks)):
                duration += float(tracks[t]['duration'])
                if tracks[t-1]['artist'] != tracks[t]['artist']:
                    is_various = True
            albums.append({
                'album': album,
                'artist': 'VA' if is_various else tracks[0]['artist'],
                'tracks': len(tracks),
                'duration': duration})
        wx.PostEvent(self.window, MpdAlbumsEvent(albums))

    """Refresh the queue"""
    def refreshQueue(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_queue,)).start()
    def __refresh_queue(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_queue()")
        queue = {}
        queue = cli.playlistid()
        if self.queue != queue:
            self.queue = queue
            wx.PostEvent(self.window, MpdQueueEvent(queue))

    """"""
    def refreshSongs(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_songs,)).start()
    def __refresh_songs(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_songs()")
        songs = {}
        songs = cli.listallinfo()
        filtered = list(filter(lambda song: song.get('directory', '') == '', songs))
        wx.PostEvent(self.window, MpdSongsEvent(filtered))

    """"""
    def refreshPlaylists(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_playlists,)).start()
    def __refresh_playlists(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_playlists()")
        playlists = {}
        playlists = cli.listplaylists()
        wx.PostEvent(self.window, MpdPlaylistsEvent(playlists))

    """"""
    def refreshAlbumArt(self, artist, album, file) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_albumart, artist, album, file)).start()
    def __refresh_albumart(self, cli: musicpd.MPDClient, artist, album, file) -> None:
        self.logger.debug("refresh_albumart()")
        album_art = {}
        offset = 0
        album_art = {'size':'1','binary':'','data':b''}
        data = b''
        while offset < int(album_art['size']):
            album_art = cli.albumart(file, offset)
            offset += int(album_art['binary'])
            data += album_art['data']
        self.__saveAlbumArt(artist, album, data)
        wx.PostEvent(self.window, MpdAlbumArtEvent(file))

    """Play the queue position"""
    def playQueuePos(self, queue_pos) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__playQueuePos, queue_pos)).start()
    def __playQueuePos(self, cli: musicpd.MPDClient, queue_pos) -> None:
        self.logger.debug("playQueuePos()")
        cli.play(queue_pos)
    """Delete the queue position"""
    def deleteQueuePos(self, queue_pos) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__deleteQueuePos, queue_pos)).start()
    def __deleteQueuePos(self, cli: musicpd.MPDClient, queue_pos) -> None:
        self.logger.debug("deleteQueuePos()")
        cli.delete(queue_pos)

    """Play the album tag"""
    def playAlbumTag(self, album_name: str) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__playAlbumTag, album_name)).start()
    def __playAlbumTag(self, cli: musicpd.MPDClient, album_name: str) -> None:
        self.logger.debug("playAlbumTag()")
        cli.clear()
        cli.findadd('(Album == "%s")' % album_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    """Append the album tag"""
    def appendAlbumTag(self, album_name: str) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__appendAlbumTag, album_name)).start()
    def __appendAlbumTag(self, cli: musicpd.MPDClient, album_name: str) -> None:
        self.logger.debug("appendAlbumTag()")
        cli.findadd('(Album == "%s")' % album_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    """Play the artist tag"""
    def playArtistTag(self, artist_name: str) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__playArtistTag, artist_name)).start()
    def __playArtistTag(self, cli: musicpd.MPDClient, artist_name: str) -> None:
        self.logger.debug("playArtistTag()")
        cli.clear()
        cli.findadd('(Artist == "%s")' % artist_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    """Append the artist tag"""
    def appendArtistTag(self, artist_name: str) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__appendArtistTag, artist_name)).start()
    def __appendArtistTag(self, cli: musicpd.MPDClient, artist_name: str) -> None:
        self.logger.debug("appendArtistTag()")
        cli.findadd('(Artist == "%s")' % artist_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    """Play the song"""
    def playSong(self, file: str) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__playSong, file)).start()
    def __playSong(self, cli: musicpd.MPDClient, file: str) -> None:
        self.logger.debug("playSong()")
        cli.clear()
        cli.add(file)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    """Append the song"""
    def appendSong(self, file: str) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__appendSong, file)).start()
    def __appendSong(self, cli: musicpd.MPDClient, file: str) -> None:
        self.logger.debug("appendSong()")
        cli.add(file)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    """Pause playing the current song"""
    def pause(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__pause,)).start()
    def __pause(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("pause()")
        cli.pause()

    """Play the current song in queue"""
    def play(self):
        threading.Thread(
            target=self.connection.execute,
            args=(self.__play,)).start()
    def __play(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("play()")
        cli.play()

    """Next song in queue"""
    def next(self):
        threading.Thread(
            target=self.connection.execute,
            args=(self.__next,)).start()
    def __next(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("next()")
        cli.next()

    """Previous song in qeueue"""
    def prev(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__prev,)).start()
    def __prev(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("prev()")
        cli.previous()

    """Set volume"""
    def setVolume(self, volume) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__setVolume, volume)).start()
    def __setVolume(self, cli: musicpd.MPDClient, volume) -> None:
        self.logger.debug("setVolume()")
        cli.setvol(volume)

    """Update"""
    def update(self) -> None:
        threading.Thread(
            target=self.connection.execute,
            args=(self.__update,)).start()
    def __update(self, cli: musicpd.MPDClient):
        self.logger.debug("update()")
        cli.update()

    """"""
    def __saveAlbumArt(self, artist, album, data):
        ext, typ = self.__getFileExtension(data)
        orig_path = self.__getArtPath(self.art_folder, self.__getArtFile(artist, album), ext)
        with open(orig_path, 'w+b') as f:
            f.write(data)
        if typ != wx.BITMAP_TYPE_PNG:
            orig_img = wx.Image(orig_path, type=typ)
            new_path = self.__getArtPath(self.art_folder, self.__getArtFile(artist, album), 'png')
            orig_img.SaveFile(new_path, wx.BITMAP_TYPE_PNG)
            os.remove(orig_path)

    """"""
    def __getFileExtension(self, data: str) -> None:
        if data.startswith(bytes.fromhex('ffd8ffe0')): # JFIF
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('ffd8ffe1')): # EXIF
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('89504e47')):
            return ('png', wx.BITMAP_TYPE_PNG)
        raise Exception(f'Unhandled file type {data[:5]}')

    """"""
    def __createArtFolder(self, folder) -> None:
        path = os.path.join(os.path.curdir, 'mpdcmd', folder)
        if not os.path.exists(path):
            os.makedirs(path)
    """"""
    def __getArtPath(self, folder, file, ext) -> str:
        return os.path.join(os.path.curdir, 'mpdcmd', folder, f"{file}.{ext}")
    """"""
    def __getArtFile(self, artist, album) -> str:
        file = '%s-%s' % (artist, album)
        # lazy fix for invalid filename characters
        return base64.urlsafe_b64encode(file.encode())
    """"""
    def getDefaultAlbumArt(self) -> wx.Bitmap:
        path = self.__getArtPath('icons', 'icon', 'png')
        return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()

    """"""
    def getAlbumArt(self, artist, album) -> wx.Bitmap:
        path = self.__getArtPath(self.art_folder, self.__getArtFile(artist, album), 'png')
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
        self.logger.info("Starting %s", type(self).__name__)

        self.actions = {
            'player': self.__action_player,
            'mixer': self.__action_mixer,
            'playlist': self.__action_playlist,
            'update': self.__action_update,
            'database': self.__action_database,
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
            self.logger.debug('Idle response %s', idles)
            for idle in idles:
                if idle in self.actions.keys():
                    self.actions[idle]()
                else:
                    self.logger.warning('Unhandled idle response %s', idle)
        except TimeoutError:
            self.logger.debug('Idle timeout after %ds', self.socket_timeout)

    """"""
    def __action_player(self):
        # start/stop/seek or changed tags of current song
        self.logger.debug('Player action')
        wx.PostEvent(self.parent, MpdIdlePlayerEvent())

    """"""
    def __action_mixer(self):
        # volume has been changed
        self.logger.debug('Mixer action')
        wx.PostEvent(self.parent, MpdIdleMixerEvent())

    """"""
    def __action_playlist(self):
        # queue has been modified
        self.logger.debug('Playlist action')
        wx.PostEvent(self.parent, MpdIdlePlaylistEvent())

    """"""
    def __action_update(self):
        # update has started or finished
        self.logger.debug('Update action')
        wx.PostEvent(self.parent, MpdIdleUpdateEvent())

    """"""
    def __action_database(self):
        # database was modified
        self.logger.debug('Database action')
        wx.PostEvent(self.parent, MpdIdleDatabaseEvent())

"""The main frame for the MpdCmd application"""
class MpdCmdFrame(wx.Frame):

    """Initialise MpdCmdFrame"""
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.preferences_file = os.path.join(os.path.curdir, 'preferences.json')
        self.preferences = self.load_preferences()

        # init mpd
        self.mpd = MpdController(
            self,
            self.preferences.get('host', ''),
            self.preferences.get('port', ''),
            self.preferences.get('username', ''),
            self.preferences.get('password', ''))

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

        self.current_song_text = wx.StaticText(self.l_panel, label="Not Playing")
        self.l_sizer.Add(self.current_song_text, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)

        self.current_song_time = wx.StaticText(self.l_panel, label="00:00/00:00")
        self.l_sizer.Add(self.current_song_time, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)

        tr = self.makeTransport(self.l_panel)
        self.l_sizer.Add(tr, 0, wx.ALL|wx.ALL, 1)

        bitmap = self.mpd.getDefaultAlbumArt()
        # TODO: better solution to keep art square?
        self.art = wx.StaticBitmap(self.r_panel, wx.ID_ANY, bitmap, size=(80,80))
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

        self.refresh()

    """Refresh"""
    def refresh(self):
        self.mpd.refreshStats()
        self.mpd.refreshStatus()
        self.mpd.refreshAlbums()
        self.mpd.refreshQueue()
        self.mpd.refreshPlaylists()
        self.mpd.refreshSongs()

    """Load preferences"""
    def load_preferences(self):
        if os.path.isfile(self.preferences_file) is False:
            with open(self.preferences_file, 'w') as file:
                preferences = {"host":"","port":"","username":"","password":"","notifications":True}
                file.write(json.dumps(preferences))
        with open(self.preferences_file, 'r') as f:
            return json.loads(f.read())

    """Make the notebook"""
    def makeNotebook(self, parent) -> wx.Notebook:
        notebook = wx.Notebook(parent)

        self.queue_ctrl = wx.ListCtrl(notebook)
        self.queue_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.queue_ctrl.InsertColumn(0, "", width=20)
        self.queue_ctrl.InsertColumn(1, "Id", width=50)
        self.queue_ctrl.InsertColumn(2, "Position", width=70)
        self.queue_ctrl.InsertColumn(3, "Album", width=150)
        self.queue_ctrl.InsertColumn(4, "Artist", width=100)
        self.queue_ctrl.InsertColumn(5, "Track", width=50)
        self.queue_ctrl.InsertColumn(6, "Title", width=200)
        self.queue_ctrl.InsertColumn(7, "Duration", width=70)
        try:
            self.queue_ctrl.SetColumnsOrder([0,1,2,3,4,5,6,7])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnQueueSelect, self.queue_ctrl)
        notebook.AddPage(self.queue_ctrl, "Queue")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.queueContext, self.queue_ctrl)

        self.album_ctrl = wx.ListCtrl(notebook)
        self.album_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.album_ctrl.InsertColumn(0, "", width=20)
        self.album_ctrl.InsertColumn(1, "Album", width=150)
        self.album_ctrl.InsertColumn(2, "Artist", width=100)
        self.album_ctrl.InsertColumn(3, "Tracks", width=50)
        self.album_ctrl.InsertColumn(4, "Duration", width=50)
        try:
            self.album_ctrl.SetColumnsOrder([0,1,2,3,4])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAlbumSelect, self.album_ctrl)
        notebook.AddPage(self.album_ctrl, "Albums")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.albumsContext, self.album_ctrl)

        self.playlists_ctrl = wx.ListCtrl(notebook)
        self.playlists_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.playlists_ctrl.InsertColumn(0, "1", width=100)
        try:
            self.playlists_ctrl.SetColumnsOrder([0])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnPlaylistSelect, self.playlists_ctrl)
        notebook.AddPage(self.playlists_ctrl, "Playlists")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.playlistsContext, self.playlists_ctrl)

        self.songs_ctrl = wx.ListCtrl(notebook)
        self.songs_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.songs_ctrl.InsertColumn(0, "", width=20)
        self.songs_ctrl.InsertColumn(1, "Album", width=150)
        self.songs_ctrl.InsertColumn(2, "Artist", width=100)
        self.songs_ctrl.InsertColumn(3, "Track", width=50)
        self.songs_ctrl.InsertColumn(4, "Title", width=200)
        self.songs_ctrl.InsertColumn(5, "Duration", width=70)
        self.songs_ctrl.InsertColumn(6, "File", width=70)
        try:
            self.songs_ctrl.SetColumnsOrder([0,1,2,3,4,5,6])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnSongSelect, self.songs_ctrl)
        notebook.AddPage(self.songs_ctrl, "Songs")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.songsContext, self.songs_ctrl)

        return notebook
    """Make the transport"""
    def makeTransport(self, parent) -> wx.Panel:
        transport = wx.Panel(parent)
        tr_hori = wx.BoxSizer(wx.HORIZONTAL)

        prevButton = wx.Button(transport, label="Prev")
        self.Bind(wx.EVT_BUTTON, self.OnPrev, prevButton)
        tr_hori.Add(prevButton, 0, wx.EXPAND|wx.ALL, 1)

        self.play_button = wx.Button(transport, label="")
        self.Bind(wx.EVT_BUTTON, self.OnPlay, self.play_button)
        tr_hori.Add(self.play_button, 0, wx.EXPAND|wx.ALL, 1)

        nextButton = wx.Button(transport, label="Next")
        self.Bind(wx.EVT_BUTTON, self.OnNext, nextButton)
        tr_hori.Add(nextButton, 0, wx.EXPAND|wx.ALL, 1)

        self.current_vol = wx.Slider(transport, minValue=0, maxValue=100, style=wx.SL_VALUE_LABEL)
        self.Bind(wx.EVT_SCROLL_CHANGED, self.OnVolChanged, self.current_vol)
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.OnVolChangeStart, self.current_vol)
        self.Bind(wx.EVT_COMMAND_SCROLL_THUMBRELEASE, self.OnVolChangeEnd, self.current_vol)
        tr_hori.Add(self.current_vol, 0, wx.EXPAND|wx.ALL, 1)

        transport.SetSizer(tr_hori)
        return transport
    """Make the menu bar"""
    def makeMenuBar(self) -> None:
        file_menu = wx.Menu()
        pref_item = file_menu.Append(-1, "&Preferences", "Configure preferences")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)

        server_menu = wx.Menu()
        refresh_item = server_menu.Append(-1, "&Refresh", "Refresh from server")
        update_item = server_menu.Append(-1, "&Update", "Trigger a server update")

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT)

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(server_menu, "&Server")
        menu_bar.Append(help_menu, "&Help")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.OnMenuPref, pref_item)
        self.Bind(wx.EVT_MENU, self.OnMenuExit, exit_item)
        self.Bind(wx.EVT_MENU, self.OnMenuRefresh, refresh_item)
        self.Bind(wx.EVT_MENU, self.OnMenuUpdate, update_item)
        self.Bind(wx.EVT_MENU, self.OnMenuAbout, about_item)

    """Convert seconds to time"""
    def secondsToTime(self, seconds: float) -> str:
        return "%02d:%02d" % (seconds//60, seconds%60)

    """On timer tick"""
    def OnTick(self, _event: wx.TimerEvent) -> None:
        self.logger.debug("OnTick")
        if self.playing:
            self.elapsed += 1
        self.updateCurrentSongTimeText()

    """MPD connection changed"""
    def OnConnectionChanged(self, event: MpdConnectionEvent) -> None:
        self.connection_status = event.GetValue()
        self.logger.info("Connection changed %s", self.connection_status)
        self.updateStatusBarText()
    """MPD stats changed"""
    def OnStatsChanged(self, event: MpdStatsEvent) -> None:
        self.stats = event.GetValue()
        self.logger.info("Stats changed %s", self.stats)
        self.update_title()
    """MPD status changed"""
    def OnStatusChanged(self, event: MpdStatusEvent) -> None:
        self.status = event.GetValue()
        self.logger.info("Status changed %s", self.status)
        self.updateStatus()
        self.mpd.refreshCurrentSong()
    """MPD songs changed"""
    def OnSongsChanged(self, event: MpdSongsEvent) -> None:
        songs = event.GetValue()
        self.logger.info("Songs changed %s", len(songs))
        self.songs_ctrl.DeleteAllItems()
        for song in songs:
            prefix = ''
            self.songs_ctrl.Append([
                prefix,
                song.get('album', ''),
                song.get('artist', ''),
                song.get('track', ''),
                song.get('title', ''),
                self.secondsToTime(float(song.get('duration', ''))),
                song.get('file', '')])
    """MPD playlists changed"""
    def OnPlaylistsChanged(self, event: MpdPlaylistsEvent) -> None:
        playlists = event.GetValue()
        self.logger.info("Playlists changed %s", playlists)
        self.playlists_ctrl.DeleteAllItems()
        for playlist in playlists:
            self.playlists_ctrl.Append(playlist)
    """MPD albumart changed"""
    def OnAlbumArtChanged(self, event: MpdAlbumArtEvent) -> None:
        songid = event.GetValue()
        self.logger.info("Albumart changed %s", songid)
        self.setCurrentAlbumArt()

    """"""
    def queueContext(self, event):
        self.logger.debug("queueContext()")
        menu = wx.Menu()
        delete_item = menu.Append(-1, "Delete")
        self.Bind(wx.EVT_MENU, self.OnMenuQueueDelete, delete_item)
        play_item = menu.Append(-1, "Play")
        self.Bind(wx.EVT_MENU, self.OnMenuQueuePlay, play_item)
        self.PopupMenu(menu, event.GetPoint())
    """"""
    def albumsContext(self, event):
        self.logger.debug("albumsContext()")
        menu = wx.Menu()
        append_item = menu.Append(-1, "Append")
        self.Bind(wx.EVT_MENU, self.OnMenuAlbumsAppend, append_item)
        play_item = menu.Append(-1, "Play")
        self.Bind(wx.EVT_MENU, self.OnMenuAlbumsPlay, play_item)
        self.PopupMenu(menu, event.GetPoint())
    """"""
    def playlistsContext(self, _event):
        self.logger.debug("playlistsContext()")
    """"""
    def songsContext(self, event):
        self.logger.debug("songsContext()")
        menu = wx.Menu()
        append_item = menu.Append(-1, "Append Song")
        self.Bind(wx.EVT_MENU, self.OnMenuSongsAppendSong, append_item)
        play_item = menu.Append(-1, "Play Song")
        self.Bind(wx.EVT_MENU, self.OnMenuSongsPlaySong, play_item)
        append_album_item = menu.Append(-1, "Append Album")
        self.Bind(wx.EVT_MENU, self.OnMenuSongsAppendAlbum, append_album_item)
        play_album_item = menu.Append(-1, "Play Album")
        self.Bind(wx.EVT_MENU, self.OnMenuSongsPlayAlbum, play_album_item)
        append_artist_item = menu.Append(-1, "Append Artist")
        self.Bind(wx.EVT_MENU, self.OnMenuSongsAppendArtist, append_artist_item)
        play_artist_item = menu.Append(-1, "Play Artist")
        self.Bind(wx.EVT_MENU, self.OnMenuSongsPlayArtist, play_artist_item)
        self.PopupMenu(menu, event.GetPoint())

    """MPD current song changed"""
    def OnCurrentSongChanged(self, event: MpdCurrentSongEvent) -> None:
        self.current_song = event.GetValue()
        self.logger.info("Song changed %s", self.current_song)
        self.mpd.refreshAlbumArt(
            self.current_song.get('artist', ''),
            self.current_song.get('album', ''),
            self.current_song.get('file', ''))
        self.updateCurrentSong()
    """Albums changed"""
    def OnAlbumsChanged(self, event: MpdAlbumsEvent) -> None:
        albums = event.GetValue()
        self.logger.info("Albums changed %d", len(albums))
        self.album_ctrl.DeleteAllItems()
        for album in albums:
            self.album_ctrl.Append([
                '',
                album.get('album', ''),
                album.get('artist', ''),
                album.get('tracks', ''),
                self.secondsToTime(float(album.get('duration', '')))])
    """Queue changed"""
    def OnQueueChanged(self, event: MpdQueueEvent) -> None:
        queue = event.GetValue()
        self.logger.info("Queue changed %s", len(queue))
        self.queue_ctrl.DeleteAllItems()
        for s in range(0, len(queue)):
            prefix = ''
            if self.current_song.get('pos', '') == str(s):
                prefix = '>'
            self.queue_ctrl.Append([
                prefix,queue[s]['id'],
                queue[s]['pos'],
                queue[s]['album'],
                queue[s]['artist'],
                queue[s]['track'],
                queue[s]['title'],
                self.secondsToTime(float(queue[s]['duration']))])

    """Idle player event"""
    def OnIdlePlayer(self, _event: MpdIdlePlayerEvent) -> None:
        self.logger.debug("Idle player")
        self.mpd.refreshStatus()
    """Idle mixer event"""
    def OnIdleMixer(self, _event: MpdIdleMixerEvent) -> None:
        self.logger.debug("Idle mixer")
        self.mpd.refreshStatus()
    """Idle playlist event"""
    def OnIdlePlaylist(self, _event: MpdIdlePlaylistEvent) -> None:
        self.logger.debug("Idle playlist")
        self.mpd.refreshQueue()
    """Idle update event"""
    def OnIdleUpdate(self, _event: MpdIdleUpdateEvent) -> None:
        self.logger.debug("Idle update")
    """Idle database event"""
    def OnIdleDatabase(self, _event: MpdIdleDatabaseEvent) -> None:
        self.logger.debug("Idle database")
        # TODO: refresh albums and songs?

    """Album item selected"""
    def OnAlbumSelect(self, _event: wx.ListEvent) -> None:
        album_name = self.album_ctrl.GetItem(
            self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Album selected %s", album_name)
        self.mpd.playAlbumTag(album_name)
    """Queue item selected"""
    def OnQueueSelect(self, _event: wx.ListEvent) -> None:
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item selected %s", queue_pos)
        self.mpd.playQueuePos(queue_pos)
    """Playlist item selected"""
    def OnPlaylistSelect(self, _event: wx.ListEvent):
        playlist = self.playlists_ctrl.GetItem(
            self.playlists_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Playlist selected %s", playlist)
    """Song item selected"""
    def OnSongSelect(self, _event: wx.ListEvent):
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Song selected %s", song)

    """Update the title text"""
    def update_title(self) -> None:
        self.Title = "MPDCMD [Artists %s Albums %s Songs %s]" % (
            self.stats.get('artists', '?'),
            self.stats.get('albums', '?'),
            self.stats.get('songs', '?'))
    """Update status related ui"""
    def updateStatus(self) -> None:
        self.updatePlayPause()
        self.updateVolume()
        self.updateSongTime()
    """Update play/pause button label"""
    def updatePlayPause(self) -> None:
        if self.status.get('state', '') != 'play':
            self.play_button.SetLabel("Play")
            self.playing = False
        else:
            self.play_button.SetLabel("Pause")
            self.playing = True
    """Update the volume slider value"""
    def updateVolume(self) -> None:
        if not self.volume_changing:
            self.current_vol.SetValue(int(self.status.get('volume', '0')))
    """Update song time"""
    def updateSongTime(self) -> None:
        self.elapsed = float(self.status.get('elapsed', '0'))
        self.duration = float(self.status.get('duration', '0'))
        self.updateCurrentSongTimeText()
    """Update current song"""
    def updateCurrentSong(self) -> None:
        for s in range(0, self.queue_ctrl.GetItemCount()):
            pos = self.queue_ctrl.GetItem(s, col=2).GetText()
            if self.current_song.get('pos', '') == str(pos):
                self.queue_ctrl.SetItem(s, 0, '>')
            else:
                self.queue_ctrl.SetItem(s, 0, ' ')
        self.showNotification()
        self.setCurrentAlbumArt()
        self.current_song_text.SetLabel("%s. %s - %s (%s)" % (
            self.current_song.get('track', '?'),
            self.current_song.get('artist', '?'),
            self.current_song.get('title', '?'),
            self.current_song.get('album', '?')))
        self.updateStatusBarText()
    """Show notification"""
    def showNotification(self) -> None:
        if self.preferences.get('notifications', True):
            notification = wx.adv.NotificationMessage(
                "MPDCMD", "%s. %s - %s\r\n%s" % (
                    self.current_song.get('track', '?'),
                    self.current_song.get('artist', '?'),
                    self.current_song.get('title', '?'),
                    self.current_song.get('album', '?')))
            bitmap = self.mpd.getAlbumArt(
                self.current_song.get('artist', ''),
                self.current_song.get('album', ''))
            notification.SetIcon(wx.Icon(bitmap))
            notification.Show(5)
    """Set the album art image for the currently playing song"""
    def setCurrentAlbumArt(self) -> None:
        bitmap = self.mpd.getAlbumArt(
            self.current_song.get('artist', ''),
            self.current_song.get('album', ''))
        self.art.Bitmap = bitmap

    """Update status bar text"""
    def updateStatusBarText(self) -> None:
        self.SetStatusText("%s %s | %s:%s %s" % (
            self.current_song.get('file', 'FILE'),
            self.current_song.get('format', 'FORMAT'),
            self.mpd.host,
            self.mpd.port,
            self.connection_status))
    """Update current song time text"""
    def updateCurrentSongTimeText(self):
        elapsed = self.secondsToTime(self.elapsed)
        duration = self.secondsToTime(self.duration)
        self.current_song_time.SetLabel("%s/%s" % (elapsed, duration))

    """Play/pause clicked"""
    def OnPlay(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnPlay()")
        if self.status.get('state', '') != 'play':
            self.mpd.play()
        else:
            self.mpd.pause()
    """Next clicked"""
    def OnNext(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnNext()")
        self.mpd.next()
    """Previous clicked"""
    def OnPrev(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnPrev()")
        self.mpd.prev()
    """Volume slider changed"""
    def OnVolChanged(self, _event: wx.CommandEvent) -> None:
        vol = self.current_vol.GetValue()
        self.mpd.setVolume(int(vol))
    def OnVolChangeStart(self, _event) -> None:
        self.volume_changing = True
    def OnVolChangeEnd(self, _event) -> None:
        self.volume_changing = False

    """Preferences menu selected"""
    def OnMenuPref(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuPref()")
        preferences = MpdPreferencesFrame(
            self.preferences,
            self,
            title='Preferences',
            size=(320,300))
        preferences.Show()
    """About menu selected"""
    def OnMenuAbout(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuAbout()")
        wx.MessageBox(
            "Music Player Daemon Command\r\nWxPython MPD Client",
            "About",
            wx.OK|wx.ICON_INFORMATION)
    """Refresh menu selected"""
    def OnMenuRefresh(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuRefresh()")
        self.refresh()
    """Update menu selected"""
    def OnMenuUpdate(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnMenuUpdate()")
        self.mpd.update()
        wx.MessageBox("Update triggered", "Update", wx.OK|wx.ICON_INFORMATION)
    """Exit menu selected"""
    def OnMenuExit(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OMenuExit()")
        self.Close(True)
    """On window/frame close"""
    def OnClose(self, _event: wx.CommandEvent) -> None:
        self.logger.debug("OnClose()")
        if self.mpd:
            self.mpd.stop()
        self.timer.Stop()
        self.Destroy()

    """Menu Queue Delete"""
    def OnMenuQueueDelete(self, _event: wx.CommandEvent) -> None:
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item delete %s", queue_pos)
        self.mpd.deleteQueuePos(queue_pos)
    """Menu Queue Play"""
    def OnMenuQueuePlay(self, _event: wx.CommandEvent) -> None:
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item play %s", queue_pos)
        self.mpd.playQueuePos(queue_pos)

    """"""
    def OnMenuAlbumsAppend(self, _event) -> None:
        album_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Albums item append %s", album_name)
        self.mpd.appendAlbumTag(album_name)
    """"""
    def OnMenuAlbumsPlay(self, _event) -> None:
        album_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Albums item play %s", album_name)
        self.mpd.playAlbumTag(album_name)

    """"""
    def OnMenuSongsAppendSong(self, _event) -> None:
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Songs item append song %s", song)
        self.mpd.appendSong(song)
    """"""
    def OnMenuSongsPlaySong(self, _event) -> None:
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Song item play song %s", song)
        self.mpd.playSong(song)
    """"""
    def OnMenuSongsAppendAlbum(self, _event) -> None:
        album = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Songs item append album %s", album)
        self.mpd.appendAlbumTag(album)
    """"""
    def OnMenuSongsPlayAlbum(self, _event) -> None:
        album = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Song item play album %s", album)
        self.mpd.playAlbumTag(album)
    """"""
    def OnMenuSongsAppendArtist(self, _event) -> None:
        artist = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Songs item append artist %s", artist)
        self.mpd.appendArtistTag(artist)
    """"""
    def OnMenuSongsPlayArtist(self, _event) -> None:
        artist = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Song item play artist %s", artist)
        self.mpd.playArtistTag(artist)

"""Mpd main window"""
class MpdPreferencesFrame(wx.Frame):
    def __init__(self, preferences, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.preferences = preferences

        self.panel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        host_label = wx.StaticText(self.panel, label='Host')
        self.sizer.Add(host_label, 0, wx.EXPAND|wx.ALL, 1)

        host_text = wx.TextCtrl(self.panel, value=self.preferences.get('host', ''))
        self.sizer.Add(host_text, 0, wx.EXPAND|wx.ALL, 1)

        port_label = wx.StaticText(self.panel, label='Port')
        self.sizer.Add(port_label, 0, wx.EXPAND|wx.ALL, 1)

        port_text = wx.TextCtrl(self.panel, value=self.preferences.get('port', ''))
        self.sizer.Add(port_text, 0, wx.EXPAND|wx.ALL, 1)

        username_label = wx.StaticText(self.panel, label='Username')
        self.sizer.Add(username_label, 0, wx.EXPAND|wx.ALL, 1)

        username_text = wx.TextCtrl(self.panel, value=self.preferences.get('username', ''))
        self.sizer.Add(username_text, 0, wx.EXPAND|wx.ALL, 1)

        password_label = wx.StaticText(self.panel, label='Password')
        self.sizer.Add(password_label, 0, wx.EXPAND|wx.ALL, 1)

        password_text = wx.TextCtrl(self.panel, value=self.preferences.get('password', ''))
        self.sizer.Add(password_text, 0, wx.EXPAND|wx.ALL, 1)

        notifications_label = wx.StaticText(self.panel, label='Notifications')
        self.sizer.Add(notifications_label, 0, wx.EXPAND|wx.ALL, 1)

        notifications_check = wx.CheckBox(self.panel)
        notifications_check.SetValue(self.preferences.get('notifications', True))
        self.sizer.Add(notifications_check, 0, wx.EXPAND|wx.ALL, 1)

        cancel_button = wx.Button(self.panel, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_button)
        self.sizer.Add(cancel_button, 0, wx.EXPAND|wx.ALL, 1)

        save_button = wx.Button(self.panel, label="Save")
        self.Bind(wx.EVT_BUTTON, self.OnSave, save_button)
        self.sizer.Add(save_button, 0, wx.EXPAND|wx.ALL, 1)

    """On save preferences"""
    def OnSave(self, _event: wx.PyCommandEvent) -> None:
        self.logger.debug("OnSave()")

    """On cancel preferences window"""
    def OnCancel(self, _event: wx.PyCommandEvent) -> None:
        self.logger.debug("OnCancel()")

"""Main function for mpdcmd"""
def main():
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    frame.SetIcon(get_icon('icon'))
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
