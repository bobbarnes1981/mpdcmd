import base64
import json
import logging
import os
import threading
import musicpd
import wx
import wx.adv
from pynput.keyboard import Listener, Key

DEFAULT_OPTION_NOTIFICATIONS = False
DEFAULT_OPTION_MEDIAKEYS = False

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

class MpdConnection():
    """Handles executing requests to MPD"""

    def __init__(self, window: wx.Window, host: str, port: str, username: str, password: str):
        """Initialise the MpdConnection"""
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

    def execute(self, func: callable, *args):
        """Execute the provided function with a connected client"""
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

class MpdController():
    """Provides interface to MPD"""

    def __init__(self, window: wx.Window, host: str, port: str, username: str, password:str):
        """Initialise the MpdController"""
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

    def start(self) -> None:
        """Start the background thread"""
        self.logger.info("Starting thread")
        self.idle_thread = MpdIdleThread(self.window, self.connection)
        self.idle_thread.start()

    def stop(self) -> None:
        """Stop the status background thread"""
        self.logger.info("Stopping thread")
        if self.idle_thread:
            self.idle_thread.stop()

    def refreshStats(self) -> None:
        """Refresh the stats"""
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

    def refreshStatus(self) -> None:
        """Refresh the status info"""
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

    def refreshCurrentSong(self) -> None:
        """Refresh the current song"""
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

    def refreshAlbums(self) -> None:
        """Refresh albums"""
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

    def refreshQueue(self) -> None:
        """Refresh the queue"""
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

    def refreshSongs(self) -> None:
        """"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_songs,)).start()
    def __refresh_songs(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_songs()")
        songs = {}
        songs = cli.listallinfo()
        filtered = list(filter(lambda song: song.get('directory', '') == '', songs))
        wx.PostEvent(self.window, MpdSongsEvent(filtered))

    def refreshPlaylists(self) -> None:
        """"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_playlists,)).start()
    def __refresh_playlists(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_playlists()")
        playlists = {}
        playlists = cli.listplaylists()
        wx.PostEvent(self.window, MpdPlaylistsEvent(playlists))

    def refreshAlbumArt(self, artist, album, file) -> None:
        """"""
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

    def playQueuePos(self, queue_pos) -> None:
        """Play the queue position"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__playQueuePos, queue_pos)).start()
    def __playQueuePos(self, cli: musicpd.MPDClient, queue_pos) -> None:
        self.logger.debug("playQueuePos()")
        cli.play(queue_pos)
    def deleteQueuePos(self, queue_pos) -> None:
        """Delete the queue position"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__deleteQueuePos, queue_pos)).start()
    def __deleteQueuePos(self, cli: musicpd.MPDClient, queue_pos) -> None:
        self.logger.debug("deleteQueuePos()")
        cli.delete(queue_pos)
    def clearQueue(self) -> None:
        """Clear the queue"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__clearQueue,)).start()
    def __clearQueue(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("clearQueue()")
        cli.clear()

    def playAlbumTag(self, album_name: str) -> None:
        """Play the album tag"""
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

    def appendAlbumTag(self, album_name: str) -> None:
        """Append the album tag"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__appendAlbumTag, album_name)).start()
    def __appendAlbumTag(self, cli: musicpd.MPDClient, album_name: str) -> None:
        self.logger.debug("appendAlbumTag()")
        cli.findadd('(Album == "%s")' % album_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def playArtistTag(self, artist_name: str) -> None:
        """Play the artist tag"""
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

    def appendArtistTag(self, artist_name: str) -> None:
        """Append the artist tag"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__appendArtistTag, artist_name)).start()
    def __appendArtistTag(self, cli: musicpd.MPDClient, artist_name: str) -> None:
        self.logger.debug("appendArtistTag()")
        cli.findadd('(Artist == "%s")' % artist_name)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def playSong(self, file: str) -> None: 
        """Play the song"""
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

    def appendSong(self, file: str) -> None:
        """Append the song"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__appendSong, file)).start()
    def __appendSong(self, cli: musicpd.MPDClient, file: str) -> None:
        self.logger.debug("appendSong()")
        cli.add(file)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def pause(self) -> None:
        """Pause playing the current song"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__pause,)).start()
    def __pause(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("pause()")
        cli.pause()

    def play(self):
        """Play the current song in queue"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__play,)).start()
    def __play(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("play()")
        cli.play()

    def next(self):
        """Next song in queue"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__next,)).start()
    def __next(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("next()")
        cli.next()

    def prev(self) -> None:
        """Previous song in qeueue"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__prev,)).start()
    def __prev(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("prev()")
        cli.previous()

    def setVolume(self, volume) -> None:
        """Set volume"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__setVolume, volume)).start()
    def __setVolume(self, cli: musicpd.MPDClient, volume) -> None:
        self.logger.debug("setVolume()")
        cli.setvol(volume)

    def setRepeat(self, repeat) -> None:
        """Set repeat"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__setRepeat, repeat)).start()
    def __setRepeat(self, cli: musicpd.MPDClient, repeat) -> None:
        self.logger.debug("setRepeat()")
        cli.repeat('1' if repeat else '0')

    def setRandom(self, random) -> None:
        """Set random"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__setRandom, random)).start()
    def __setRandom(self, cli: musicpd.MPDClient, random) -> None:
        self.logger.debug("setRandom()")
        cli.random('1' if random else '0')

    def setSingle(self, single) -> None:
        """Set single"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__setSingle, single)).start()
    def __setSingle(self, cli: musicpd.MPDClient, single) -> None:
        self.logger.debug("setSingle()")
        cli.single('1' if single else '0')

    def setConsume(self, consume) -> None:
        """Set consume"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__setConsume, consume)).start()
    def __setConsume(self, cli: musicpd.MPDClient, consume) -> None:
        self.logger.debug("setConsume()")
        cli.consume(consume)

    def update(self) -> None:
        """Update"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__update,)).start()
    def __update(self, cli: musicpd.MPDClient):
        self.logger.debug("update()")
        cli.update()

    def __saveAlbumArt(self, artist, album, data):
        """"""
        ext, typ = self.__getFileExtension(data)
        orig_path = self.__getArtPath(self.art_folder, self.__getArtFile(artist, album), ext)
        with open(orig_path, 'w+b') as f:
            f.write(data)
        if typ != wx.BITMAP_TYPE_PNG:
            orig_img = wx.Image(orig_path, type=typ)
            new_path = self.__getArtPath(self.art_folder, self.__getArtFile(artist, album), 'png')
            orig_img.SaveFile(new_path, wx.BITMAP_TYPE_PNG)
            os.remove(orig_path)

    def __getFileExtension(self, data: str) -> None:
        """"""
        if data.startswith(bytes.fromhex('ffd8ffe0')): # JFIF
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('ffd8ffe1')): # EXIF
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('89504e47')):
            return ('png', wx.BITMAP_TYPE_PNG)
        raise Exception(f'Unhandled file type {data[:5]}')

    def __createArtFolder(self, folder) -> None:
        """"""
        path = os.path.join(os.path.curdir, 'mpdcmd', folder)
        if not os.path.exists(path):
            os.makedirs(path)
    def __getArtPath(self, folder, file, ext) -> str:
        """"""
        return os.path.join(os.path.curdir, 'mpdcmd', folder, f"{file}.{ext}")
    def __getArtFile(self, artist, album) -> str:
        """"""
        file = '%s-%s' % (artist, album)
        # lazy fix for invalid filename characters
        return base64.urlsafe_b64encode(file.encode())
    def getDefaultAlbumArt(self) -> wx.Bitmap:
        """"""
        path = self.__getArtPath('icons', 'icon', 'png')
        return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()

    def getAlbumArt(self, artist, album) -> wx.Bitmap:
        """"""
        path = self.__getArtPath(self.art_folder, self.__getArtFile(artist, album), 'png')
        if os.path.isfile(path):
            return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()
        return self.getDefaultAlbumArt()

class MpdIdleThread(threading.Thread):
    """"""

    def __init__(self, parent: wx.Window, connection: MpdConnection):
        """Initialise the MpdIdleThread"""
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

    def run(self):
        """Start the thread (override)"""
        self.running = True
        while self.running:
            self.logger.debug("tick()")
            self.connection.execute(self.__idle)
    def stop(self) -> None:
        """Stop the thread"""
        self.running = False

    def __idle(self, cli) -> None:
        """Refresh the status info"""
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

    def __action_player(self):
        """"""
        # start/stop/seek or changed tags of current song
        self.logger.debug('Player action')
        wx.PostEvent(self.parent, MpdIdlePlayerEvent())

    def __action_mixer(self):
        """"""
        # volume has been changed
        self.logger.debug('Mixer action')
        wx.PostEvent(self.parent, MpdIdleMixerEvent())

    def __action_playlist(self):
        """"""
        # queue has been modified
        self.logger.debug('Playlist action')
        wx.PostEvent(self.parent, MpdIdlePlaylistEvent())

    def __action_update(self):
        """"""
        # update has started or finished
        self.logger.debug('Update action')
        wx.PostEvent(self.parent, MpdIdleUpdateEvent())

    def __action_database(self):
        """"""
        # database was modified
        self.logger.debug('Database action')
        wx.PostEvent(self.parent, MpdIdleDatabaseEvent())

class MpdCmdFrame(wx.Frame):
    """The main frame for the MpdCmd application"""

    def __init__(self, *args, **kw):
        """Initialise MpdCmdFrame"""
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.preferences_file = os.path.join(os.path.curdir, 'preferences.json')
        self.preferences = self.load_preferences()

        self.kbd_thread = None
        if self.preferences.get('mediakeys', DEFAULT_OPTION_MEDIAKEYS):
            self.logger.warn("Keyboard listener (pynput) enabled")
            self.kbd_thread = Listener(on_press=self.__key_press, on_release=None)
            self.kbd_thread.start()

        # init mpd
        self.mpd = MpdController(
            self,
            self.preferences.get('host', ''),
            self.preferences.get('port', ''),
            self.preferences.get('username', ''),
            self.preferences.get('password', ''))

        self.Bind(EVT_MPD_CONNECTION, self.on_connection_changed)
        self.Bind(EVT_MPD_STATS, self.on_stats_changed)
        self.Bind(EVT_MPD_STATUS, self.on_status_changed)
        self.Bind(EVT_MPD_SONGS, self.on_songs_changed)
        self.Bind(EVT_MPD_PLAYLISTS, self.on_playlists_changed)
        self.Bind(EVT_MPD_ALBUMART, self.on_album_art_changed)

        self.Bind(EVT_MPD_CTRL_CURRENTSONG, self.on_current_song_changed)
        self.Bind(EVT_MPD_CTRL_ALBUMS, self.on_albums_changed)
        self.Bind(EVT_MPD_CTRL_QUEUE, self.on_queue_changed)

        self.Bind(EVT_MPD_IDLE_PLAYER, self.on_idle_player)
        self.Bind(EVT_MPD_IDLE_MIXER, self.on_idle_mixer)
        self.Bind(EVT_MPD_IDLE_PLAYLIST, self.on_idle_playlist)
        self.Bind(EVT_MPD_IDLE_UPDATE, self.on_idle_update)
        self.Bind(EVT_MPD_IDLE_DATABASE, self.on_idle_database)

        # init properties
        self.stats = {}
        self.status = {}
        self.current_song = {}
        self.connection_status = "Not connected"
        self.volume_changing = False

        self.timer = wx.Timer(self)
        self.elapsed = 0
        self.duration = 0
        self.Bind(wx.EVT_TIMER, self.on_tick, self.timer)
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
        nb = self.make_notebook(self.top_panel)
        self.top_sizer.Add(nb, 1, wx.EXPAND|wx.ALL, 1)

        self.current_song_text = wx.StaticText(self.l_panel, label="Not Playing")
        self.l_sizer.Add(self.current_song_text, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)

        self.current_song_time = wx.StaticText(self.l_panel, label="00:00/00:00")
        self.l_sizer.Add(self.current_song_time, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 8)

        tr = self.make_transport(self.l_panel)
        self.l_sizer.Add(tr, 0, wx.ALL|wx.ALL, 1)

        bitmap = self.mpd.getDefaultAlbumArt()
        # TODO: better solution to keep art square?
        self.art = wx.StaticBitmap(self.r_panel, wx.ID_ANY, bitmap, size=(80,80))
        self.r_sizer.Add(self.art, 0, wx.EXPAND|wx.ALL, 1)

        self.logger.info("Initialising UI")

        self.make_menu_bar()
        self.CreateStatusBar()

        self.update_status()
        self.update_statusBarText()
        self.updateCurrentSongTimeText()

        self.mpd.start()
        self.timer.Start(1000, wx.TIMER_CONTINUOUS)

        self.logger.info("Refreshing MPD data")

        self.refresh()

    def __key_press(self, key) -> None:
        if key == Key.media_play_pause:
            self.OnPlay(None)
        if key == Key.media_next:
            self.OnNext(None)
        if key == Key.media_previous:
            self.OnPrev(None)
        if key == Key.media_volume_up:
            self.current_vol.SetValue(self.current_vol.GetValue()+5)
            self.OnVolChanged(None)
        if key == Key.media_volume_down:
            self.current_vol.SetValue(self.current_vol.GetValue()-5)
            self.OnVolChanged(None)

    def refresh(self):
        """Refresh"""
        self.mpd.refreshStats()
        self.mpd.refreshStatus()
        self.mpd.refreshAlbums()
        self.mpd.refreshQueue()
        self.mpd.refreshPlaylists()
        self.mpd.refreshSongs()

    def load_preferences(self):
        """Load preferences"""
        if os.path.isfile(self.preferences_file) is False:
            with open(self.preferences_file, 'w') as file:
                preferences = {
                    "host":"",
                    "port":"",
                    "username":"",
                    "password":"",
                    "notifications":DEFAULT_OPTION_NOTIFICATIONS,
                    "mediakeys":DEFAULT_OPTION_MEDIAKEYS}
                file.write(json.dumps(preferences))
        with open(self.preferences_file, 'r') as f:
            return json.loads(f.read())

    def make_notebook(self, parent) -> wx.Notebook:
        """Make the notebook"""
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
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.queue_item_activated, self.queue_ctrl)
        notebook.AddPage(self.queue_ctrl, "Queue")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.queue_context_menu, self.queue_ctrl)

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
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.album_item_activated, self.album_ctrl)
        notebook.AddPage(self.album_ctrl, "Albums")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.albums_context_menu, self.album_ctrl)

        self.playlists_ctrl = wx.ListCtrl(notebook)
        self.playlists_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.playlists_ctrl.InsertColumn(0, "1", width=100)
        try:
            self.playlists_ctrl.SetColumnsOrder([0])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.playlists_item_activated, self.playlists_ctrl)
        notebook.AddPage(self.playlists_ctrl, "Playlists")
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.playlists_context_menu, self.playlists_ctrl)

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
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.songs_context_menu, self.songs_ctrl)

        return notebook
    def make_transport(self, parent) -> wx.Panel:
        """Make the transport"""
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
        
        repeat_label = wx.StaticText(transport, label='Rpt')
        tr_hori.Add(repeat_label, 0, wx.EXPAND|wx.ALL, 1)
        self.repeat_check = wx.CheckBox(transport)
        self.repeat_check.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.OnRepeatChanged, self.repeat_check)
        tr_hori.Add(self.repeat_check, 0, wx.EXPAND|wx.ALL, 1)

        random_label = wx.StaticText(transport, label='Rnd')
        tr_hori.Add(random_label, 0, wx.EXPAND|wx.ALL, 1)
        self.random_check = wx.CheckBox(transport)
        self.random_check.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.OnRandomChanged, self.random_check)
        tr_hori.Add(self.random_check, 0, wx.EXPAND|wx.ALL, 1)

        single_label = wx.StaticText(transport, label='Sgl')
        tr_hori.Add(single_label, 0, wx.EXPAND|wx.ALL, 1)
        self.single_check = wx.CheckBox(transport)
        self.single_check.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.OnSingleChanged, self.single_check)
        tr_hori.Add(self.single_check, 0, wx.EXPAND|wx.ALL, 1)

        consume_label = wx.StaticText(transport, label='Cns')
        tr_hori.Add(consume_label, 0, wx.EXPAND|wx.ALL, 1)
        self.consume_check = wx.CheckBox(transport)
        self.consume_check.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.OnConsumeChanged, self.consume_check)
        tr_hori.Add(self.consume_check, 0, wx.EXPAND|wx.ALL, 1)

        transport.SetSizer(tr_hori)
        return transport
    def make_menu_bar(self) -> None:
        """Make the menu bar"""
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

    def seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to time"""
        return "%02d:%02d" % (seconds//60, seconds%60)

    def on_tick(self, _event: wx.TimerEvent) -> None:
        """On timer tick"""
        self.logger.debug("on_tick")
        if self.playing:
            self.elapsed += 1
        self.updateCurrentSongTimeText()

    def on_connection_changed(self, event: MpdConnectionEvent) -> None:
        """MPD connection changed"""
        self.connection_status = event.GetValue()
        self.logger.info("Connection changed %s", self.connection_status)
        self.update_statusBarText()
    def on_stats_changed(self, event: MpdStatsEvent) -> None:
        """MPD stats changed"""
        self.stats = event.GetValue()
        self.logger.info("Stats changed %s", self.stats)
        self.update_title()
    def on_status_changed(self, event: MpdStatusEvent) -> None:
        """MPD status changed"""
        self.status = event.GetValue()
        self.logger.info("Status changed %s", self.status)
        self.update_status()
        self.mpd.refreshCurrentSong()
    def on_songs_changed(self, event: MpdSongsEvent) -> None:
        """MPD songs changed"""
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
                self.seconds_to_time(float(song.get('duration', ''))),
                song.get('file', '')])
    def on_playlists_changed(self, event: MpdPlaylistsEvent) -> None:
        """MPD playlists changed"""
        playlists = event.GetValue()
        self.logger.info("Playlists changed %s", playlists)
        self.playlists_ctrl.DeleteAllItems()
        for playlist in playlists:
            self.playlists_ctrl.Append(playlist)
    def on_album_art_changed(self, event: MpdAlbumArtEvent) -> None:
        """MPD albumart changed"""
        songid = event.GetValue()
        self.logger.info("Albumart changed %s", songid)
        self.setCurrentAlbumArt()

    def queue_context_menu(self, event):
        """"""
        self.logger.debug("queue_context_menu()")
        menu = wx.Menu()
        clear_item = menu.Append(-1, "Clear")
        self.Bind(wx.EVT_MENU, self.OnMenuQueueClear, clear_item)
        delete_item = menu.Append(-1, "Delete")
        self.Bind(wx.EVT_MENU, self.OnMenuQueueDelete, delete_item)
        play_item = menu.Append(-1, "Play")
        self.Bind(wx.EVT_MENU, self.OnMenuQueuePlay, play_item)
        self.PopupMenu(menu, event.GetPoint())
    def albums_context_menu(self, event):
        """"""
        self.logger.debug("albums_context_menu()")
        menu = wx.Menu()
        append_item = menu.Append(-1, "Append")
        self.Bind(wx.EVT_MENU, self.OnMenuAlbumsAppend, append_item)
        play_item = menu.Append(-1, "Play")
        self.Bind(wx.EVT_MENU, self.OnMenuAlbumsPlay, play_item)
        self.PopupMenu(menu, event.GetPoint())
    def playlists_context_menu(self, _event):
        """"""
        self.logger.debug("playlists_context_menu()")
    def songs_context_menu(self, event):
        """"""
        self.logger.debug("songs_context_menu()")
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

    def on_current_song_changed(self, event: MpdCurrentSongEvent) -> None:
        """MPD current song changed"""
        self.current_song = event.GetValue()
        self.logger.info("Song changed %s", self.current_song)
        self.mpd.refreshAlbumArt(
            self.current_song.get('artist', ''),
            self.current_song.get('album', ''),
            self.current_song.get('file', ''))
        self.updateCurrentSong()
    def on_albums_changed(self, event: MpdAlbumsEvent) -> None:
        """Albums changed"""
        albums = event.GetValue()
        self.logger.info("Albums changed %d", len(albums))
        self.album_ctrl.DeleteAllItems()
        for album in albums:
            self.album_ctrl.Append([
                '',
                album.get('album', ''),
                album.get('artist', ''),
                album.get('tracks', ''),
                self.seconds_to_time(float(album.get('duration', '')))])
    def on_queue_changed(self, event: MpdQueueEvent) -> None:
        """Queue changed"""
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
                self.seconds_to_time(float(queue[s]['duration']))])

    def on_idle_player(self, _event: MpdIdlePlayerEvent) -> None:
        """Idle player event"""
        self.logger.debug("Idle player")
        self.mpd.refreshStatus()
    def on_idle_mixer(self, _event: MpdIdleMixerEvent) -> None:
        """Idle mixer event"""
        self.logger.debug("Idle mixer")
        self.mpd.refreshStatus()
    def on_idle_playlist(self, _event: MpdIdlePlaylistEvent) -> None:
        """Idle playlist event"""
        self.logger.debug("Idle playlist")
        self.mpd.refreshQueue()
    def on_idle_update(self, _event: MpdIdleUpdateEvent) -> None:
        """Idle update event"""
        self.logger.debug("Idle update")
    def on_idle_database(self, _event: MpdIdleDatabaseEvent) -> None:
        """Idle database event"""
        self.logger.debug("Idle database")
        # TODO: refresh albums and songs?

    def album_item_activated(self, _event: wx.ListEvent) -> None:
        """Album item selected"""
        album_name = self.album_ctrl.GetItem(
            self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Album selected %s", album_name)
        self.mpd.playAlbumTag(album_name)
    def queue_item_activated(self, _event: wx.ListEvent) -> None:
        """Queue item selected"""
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item selected %s", queue_pos)
        self.mpd.playQueuePos(queue_pos)
    def playlists_item_activated(self, _event: wx.ListEvent):
        """Playlist item selected"""
        playlist = self.playlists_ctrl.GetItem(
            self.playlists_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Playlist selected %s", playlist)
    def OnSongSelect(self, _event: wx.ListEvent):
        """Song item selected"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Song selected %s", song)

    def update_title(self) -> None:
        """Update the title text"""
        self.Title = "MPDCMD [Artists %s Albums %s Songs %s]" % (
            self.stats.get('artists', '?'),
            self.stats.get('albums', '?'),
            self.stats.get('songs', '?'))
    def update_status(self) -> None:
        """Update status related ui"""
        self.updatePlayPause()
        self.updateVolume()
        self.updateOptions()
        self.updateSongTime()
    def updatePlayPause(self) -> None:
        """Update play/pause button label"""
        if self.status.get('state', '') != 'play':
            self.play_button.SetLabel("Play")
            self.playing = False
        else:
            self.play_button.SetLabel("Pause")
            self.playing = True
    def updateVolume(self) -> None:
        """Update the volume slider value"""
        if not self.volume_changing:
            self.current_vol.SetValue(int(self.status.get('volume', '0')))
    def updateOptions(self) -> None:
        """"""
        self.repeat_check.SetValue(bool(self.status.get('repeat', '0') == '1'))
        self.random_check.SetValue(bool(self.status.get('random', '0') == '1'))
        self.single_check.SetValue(bool(self.status.get('repeat', '0') == '1'))
        self.consume_check.SetValue(bool(self.status.get('consume', '0') == '1'))
    def updateSongTime(self) -> None:
        """Update song time"""
        self.elapsed = float(self.status.get('elapsed', '0'))
        self.duration = float(self.status.get('duration', '0'))
        self.updateCurrentSongTimeText()
    def updateCurrentSong(self) -> None:
        """Update current song"""
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
        self.update_statusBarText()
    def showNotification(self) -> None:
        """Show notification"""
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
    def setCurrentAlbumArt(self) -> None:
        """Set the album art image for the currently playing song"""
        bitmap = self.mpd.getAlbumArt(
            self.current_song.get('artist', ''),
            self.current_song.get('album', ''))
        self.art.Bitmap = bitmap

    def update_statusBarText(self) -> None:
        """Update status bar text"""
        self.SetStatusText("%s %s | %s:%s %s" % (
            self.current_song.get('file', 'FILE'),
            self.current_song.get('format', 'FORMAT'),
            self.mpd.host,
            self.mpd.port,
            self.connection_status))
    def updateCurrentSongTimeText(self):
        """Update current song time text"""
        elapsed = self.seconds_to_time(self.elapsed)
        duration = self.seconds_to_time(self.duration)
        self.current_song_time.SetLabel("%s/%s" % (elapsed, duration))

    def OnPlay(self, _event: wx.CommandEvent) -> None:
        """Play/pause clicked"""
        self.logger.debug("OnPlay()")
        if self.status.get('state', '') != 'play':
            self.mpd.play()
        else:
            self.mpd.pause()
    def OnNext(self, _event: wx.CommandEvent) -> None:
        """Next clicked"""
        self.logger.debug("OnNext()")
        self.mpd.next()
    def OnPrev(self, _event: wx.CommandEvent) -> None:
        """Previous clicked"""
        self.logger.debug("OnPrev()")
        self.mpd.prev()
    def OnVolChanged(self, _event: wx.CommandEvent) -> None:
        """Volume slider changed"""
        vol = self.current_vol.GetValue()
        self.mpd.setVolume(int(vol))
    def OnVolChangeStart(self, _event) -> None:
        self.volume_changing = True
    def OnVolChangeEnd(self, _event) -> None:
        self.volume_changing = False
    def OnRepeatChanged(self, _event) -> None:
        repeat = self.repeat_check.GetValue()
        self.mpd.setRepeat(repeat)
    def OnRandomChanged(self, _event) -> None:
        random = self.random_check.GetValue()
        self.mpd.setRandom(random)
    def OnSingleChanged(self, _event) -> None:
        single = self.single_check.GetValue()
        self.mpd.setSingle(single)
    def OnConsumeChanged(self, _event) -> None:
        consume = self.consume_check.GetValue()
        self.mpd.setConsume(consume)

    def OnMenuPref(self, _event: wx.CommandEvent) -> None:
        """Preferences menu selected"""
        self.logger.debug("OnMenuPref()")
        preferences = MpdPreferencesFrame(
            self.preferences,
            self,
            title='Preferences',
            size=(320,330))
        preferences.Show()
    def OnMenuAbout(self, _event: wx.CommandEvent) -> None:
        """About menu selected"""
        self.logger.debug("OnMenuAbout()")
        wx.MessageBox(
            "Music Player Daemon Command\r\nWxPython MPD Client",
            "About",
            wx.OK|wx.ICON_INFORMATION)
    def OnMenuRefresh(self, _event: wx.CommandEvent) -> None:
        """Refresh menu selected"""
        self.logger.debug("OnMenuRefresh()")
        self.refresh()
    def OnMenuUpdate(self, _event: wx.CommandEvent) -> None:
        """Update menu selected"""
        self.logger.debug("OnMenuUpdate()")
        self.mpd.update()
        wx.MessageBox("Update triggered", "Update", wx.OK|wx.ICON_INFORMATION)
    def OnMenuExit(self, _event: wx.CommandEvent) -> None:
        """Exit menu selected"""
        self.logger.debug("OMenuExit()")
        self.Close(True)
    def OnClose(self, _event: wx.CommandEvent) -> None:
        """On window/frame close"""
        self.logger.debug("OnClose()")
        if self.mpd:
            self.mpd.stop()
        if self.kbd_thread:
            self.kbd_thread.stop()
        self.timer.Stop()
        self.Destroy()

    def OnMenuQueueClear(self, _event: wx.CommandEvent) -> None:
        """Menu Queue Clear"""
        self.logger.info("Queue clear")
        self.mpd.clearQueue()
    def OnMenuQueueDelete(self, _event: wx.CommandEvent) -> None:
        """Menu Queue Delete"""
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item delete %s", queue_pos)
        self.mpd.deleteQueuePos(queue_pos)
    def OnMenuQueuePlay(self, _event: wx.CommandEvent) -> None:
        """Menu Queue Play"""
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item play %s", queue_pos)
        self.mpd.playQueuePos(queue_pos)

    def OnMenuAlbumsAppend(self, _event) -> None:
        """"""
        album_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Albums item append %s", album_name)
        self.mpd.appendAlbumTag(album_name)
    def OnMenuAlbumsPlay(self, _event) -> None:
        """"""
        album_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Albums item play %s", album_name)
        self.mpd.playAlbumTag(album_name)

    def OnMenuSongsAppendSong(self, _event) -> None:
        """"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Songs item append song %s", song)
        self.mpd.appendSong(song)
    def OnMenuSongsPlaySong(self, _event) -> None:
        """"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Song item play song %s", song)
        self.mpd.playSong(song)
    def OnMenuSongsAppendAlbum(self, _event) -> None:
        """"""
        album = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Songs item append album %s", album)
        self.mpd.appendAlbumTag(album)
    def OnMenuSongsPlayAlbum(self, _event) -> None:
        """"""
        album = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Song item play album %s", album)
        self.mpd.playAlbumTag(album)
    def OnMenuSongsAppendArtist(self, _event) -> None:
        """"""
        artist = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Songs item append artist %s", artist)
        self.mpd.appendArtistTag(artist)
    def OnMenuSongsPlayArtist(self, _event) -> None:
        """"""
        artist = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Song item play artist %s", artist)
        self.mpd.playArtistTag(artist)

class MpdPreferencesFrame(wx.Frame):
    """Mpd main window"""
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
        notifications_check.SetValue(self.preferences.get('notifications', DEFAULT_OPTION_NOTIFICATIONS))
        self.sizer.Add(notifications_check, 0, wx.EXPAND|wx.ALL, 1)

        mediakeys_label = wx.StaticText(self.panel, label='Media Keys')
        self.sizer.Add(mediakeys_label, 0, wx.EXPAND|wx.ALL, 1)

        mediakeys_check = wx.CheckBox(self.panel)
        mediakeys_check.SetValue(self.preferences.get('mediakeys', DEFAULT_OPTION_MEDIAKEYS))
        self.sizer.Add(mediakeys_check, 0, wx.EXPAND|wx.ALL, 1)

        cancel_button = wx.Button(self.panel, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.sizer.Add(cancel_button, 0, wx.EXPAND|wx.ALL, 1)

        save_button = wx.Button(self.panel, label="Save")
        self.Bind(wx.EVT_BUTTON, self.on_save, save_button)
        self.sizer.Add(save_button, 0, wx.EXPAND|wx.ALL, 1)

    def on_save(self, _event: wx.PyCommandEvent) -> None:
        """On save preferences"""
        self.logger.debug("on_save()")

    def on_cancel(self, _event: wx.PyCommandEvent) -> None:
        """On cancel preferences window"""
        self.logger.debug("on_cancel()")

def main():
    """The main function for MPDCMD"""
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    frame.SetIcon(get_icon('icon'))
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
