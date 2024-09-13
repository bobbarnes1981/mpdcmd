"""MPD CMD - Music player daemon client"""
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
DEFAULT_OPTION_FETCHALLART = False

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_icon(file):
    """Get the icon"""
    icon = wx.Icon()
    icon.LoadFile(
        os.path.join(os.path.curdir, 'mpdcmd', 'icons', f"{file}.png"),
        type=wx.BITMAP_TYPE_PNG)
    return icon

mcEVT_MPD_CONNECTION = wx.NewEventType()
EVT_MPD_CONNECTION = wx.PyEventBinder(mcEVT_MPD_CONNECTION, 1)
class MpdConnectionEvent(wx.PyCommandEvent):
    """MPD connection event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: str):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CONNECTION, -1)
        self._value = value
    def get_value(self) -> str:
        """Get the value"""
        return self._value

mcEVT_MPD_STATS = wx.NewEventType()
EVT_MPD_STATS = wx.PyEventBinder(mcEVT_MPD_STATS, 1)
class MpdStatsEvent(wx.PyCommandEvent):
    """MPD stats event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: dict):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_STATS, -1)
        self._value = value
    def get_value(self) -> dict:
        """Get the value"""
        return self._value

mcEVT_MPD_STATUS = wx.NewEventType()
EVT_MPD_STATUS = wx.PyEventBinder(mcEVT_MPD_STATUS, 1)
class MpdStatusEvent(wx.PyCommandEvent):
    """MPD status event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: dict):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_STATUS, -1)
        self._value = value
    def get_value(self) -> dict:
        """Get the value"""
        return self._value

mcEVT_MPD_SONGS = wx.NewEventType()
EVT_MPD_SONGS = wx.PyEventBinder(mcEVT_MPD_SONGS, 1)
class MpdSongsEvent(wx.PyCommandEvent):
    """MPD songs event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: list):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_SONGS, -1)
        self._value = value
    def get_value(self) -> list:
        """Get the value"""
        return self._value
    
mcEVT_MPD_SEARCH = wx.NewEventType()
EVT_MPD_SEARCH = wx.PyEventBinder(mcEVT_MPD_SEARCH, 1)
class MpdSearchEvent(wx.PyCommandEvent):
    """MPD search event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: list):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_SEARCH, -1)
        self._value = value
    def get_value(self) -> list:
        """Get the value"""
        return self._value

mcEVT_MPD_PLAYLISTS = wx.NewEventType()
EVT_MPD_PLAYLISTS = wx.PyEventBinder(mcEVT_MPD_PLAYLISTS, 1)
class MpdPlaylistsEvent(wx.PyCommandEvent):
    """MPD playlists event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: list):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_PLAYLISTS, -1)
        self._value = value
    def get_value(self) -> list:
        """Get the value"""
        return self._value

mcEVT_MPD_ALBUMART = wx.NewEventType()
EVT_MPD_ALBUMART = wx.PyEventBinder(mcEVT_MPD_ALBUMART, 1)
class MpdAlbumArtEvent(wx.PyCommandEvent):
    """MPD albums event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: str):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_ALBUMART, -1)
        self._value = value
    def get_value(self) -> str:
        """Get the value"""
        return self._value

mcEVT_MPD_CTRL_CURRENTSONG = wx.NewEventType()
EVT_MPD_CTRL_CURRENTSONG = wx.PyEventBinder(mcEVT_MPD_CTRL_CURRENTSONG, 1)
class MpdCurrentSongEvent(wx.PyCommandEvent):
    """MPD current song event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: dict):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CTRL_CURRENTSONG, -1)
        self._value = value
    def get_value(self) -> dict:
        """Get the value"""
        return self._value

mcEVT_MPD_CTRL_QUEUE = wx.NewEventType()
EVT_MPD_CTRL_QUEUE = wx.PyEventBinder(mcEVT_MPD_CTRL_QUEUE, 1)
class MpdQueueEvent(wx.PyCommandEvent):
    """MPD queue event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: list):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CTRL_QUEUE, -1)
        self._value = value
    def get_value(self) -> list:
        """Get the value"""
        return self._value

mcEVT_MPD_CTRL_ALBUMS = wx.NewEventType()
EVT_MPD_CTRL_ALBUMS = wx.PyEventBinder(mcEVT_MPD_CTRL_ALBUMS, 1)
class MpdAlbumsEvent(wx.PyCommandEvent):
    """MPD albums event"""
    # pylint: disable=too-few-public-methods
    def __init__(self, value: list):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_CTRL_ALBUMS, -1)
        self._value = value
    def get_value(self) -> list:
        """Get the value"""
        return self._value

mcEVT_MPD_IDLE_PLAYER = wx.NewEventType()
EVT_MPD_IDLE_PLAYER = wx.PyEventBinder(mcEVT_MPD_IDLE_PLAYER, 1)
class MpdIdlePlayerEvent(wx.PyCommandEvent):
    """MPD idle player event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_PLAYER, -1)

mcEVT_MPD_IDLE_MIXER = wx.NewEventType()
EVT_MPD_IDLE_MIXER = wx.PyEventBinder(mcEVT_MPD_IDLE_MIXER, 1)
class MpdIdleMixerEvent(wx.PyCommandEvent):
    """MPD idle mixer event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_MIXER, -1)

mcEVT_MPD_IDLE_PLAYLIST = wx.NewEventType()
EVT_MPD_IDLE_PLAYLIST = wx.PyEventBinder(mcEVT_MPD_IDLE_PLAYLIST, 1)
class MpdIdlePlaylistEvent(wx.PyCommandEvent):
    """MPD idle playlists event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_PLAYLIST, -1)

mcEVT_MPD_IDLE_UPDATE = wx.NewEventType()
EVT_MPD_IDLE_UPDATE = wx.PyEventBinder(mcEVT_MPD_IDLE_UPDATE, 1)
class MpdIdleUpdateEvent(wx.PyCommandEvent):
    """MPD idle update event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_UPDATE, -1)

mcEVT_MPD_IDLE_DATABASE = wx.NewEventType()
EVT_MPD_IDLE_DATABASE = wx.PyEventBinder(mcEVT_MPD_IDLE_DATABASE, 1)
class MpdIdleDatabaseEvent(wx.PyCommandEvent):
    """MPD idle database event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_DATABASE, -1)

mcEVT_MPD_IDLE_OPTIONS = wx.NewEventType()
EVT_MPD_IDLE_OPTIONS = wx.PyEventBinder(mcEVT_MPD_IDLE_OPTIONS, 1)
class MpdIdleOptionsEvent(wx.PyCommandEvent):
    """MPD idle options event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_OPTIONS, -1)
        
mcEVT_MPD_IDLE_STOREDPLAYLIST = wx.NewEventType()
EVT_MPD_IDLE_STOREDPLAYLIST = wx.PyEventBinder(mcEVT_MPD_IDLE_STOREDPLAYLIST, 1)
class MpdIdleStoredPlaylistEvent(wx.PyCommandEvent):
    """MPD idle stored_playlist event"""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialise the event"""
        wx.PyCommandEvent.__init__(self, mcEVT_MPD_IDLE_STOREDPLAYLIST, -1)

def albums_from_listallinfo(cli: musicpd.MPDClient) -> list:
    songs_result = cli.listallinfo()
    album_dict = {}
    for song in songs_result:
        if 'directory' in song:
            continue
        if song['album'] not in album_dict:
            album_dict[song['album']] = {
                'album': song['album'],
                'artist': song.get('albumartist', song.get('artist', '')),
                'tracks': 0,
                'duration': 0}
        album_dict[song['album']]['tracks']+=1
        album_dict[song['album']]['duration']+=float(song['duration'])
    return list(album_dict.values())

class MpdConnection():
    """Handles executing requests to MPD"""
    # pylint: disable=too-few-public-methods
    def __init__(self, window: wx.Window, config: dict):
        """Initialise the MpdConnection"""
        self.window = window
        self.host = config.get('host', '')
        self.port = config.get('port', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')

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
        except musicpd.ConnectionError as e:
            connection_status = "Connection error"
            self.logger.warning("Connection error %s %s", func.__name__, args)
            self.logger.warning(e)
        except musicpd.CommandError as e:
            self.logger.warning("Command error %s %s", func.__name__, args)
            for arg in e.args:
                self.logger.warning(arg)
        if self.connection_status != connection_status:
            self.connection_status = connection_status
            wx.PostEvent(self.window, MpdConnectionEvent(connection_status))

class MpdController():
    """Provides interface to MPD"""
    # pylint: disable=too-many-public-methods
    def __init__(self, window: wx.Window):
        """Initialise the MpdController"""
        self.window = window

        self.art_folder = 'albumart'

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.connection = None

        self.stats = {}
        self.status = {}
        self.queue = []
        self.current_song = {}
        self.albums = []

        self.art_enabled = True
        self.art_thread = None
        self.idle_thread = None

        self.__create_art_folder(self.art_folder)

    def start(self) -> None:
        """Start the background thread"""
        self.logger.info("Starting thread")
        self.idle_thread = MpdIdleThread(self)
        self.idle_thread.start()

    def stop(self) -> None:
        """Stop the status background threads"""
        self.logger.info("Stopping threads")
        if self.art_enabled:
            self.art_enabled = False
        if self.idle_thread:
            self.idle_thread.stop()

    def refresh_stats(self) -> None:
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

    def refresh_status(self) -> None:
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

    def refresh_current_song(self) -> None:
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

    def refresh_albums(self) -> None:
        """Refresh albums"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_albums,)).start()
    def __refresh_albums(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_albums()")
        albums = albums_from_listallinfo(cli)
        if self.albums != albums:
            self.albums = albums
            wx.PostEvent(self.window, MpdAlbumsEvent(self.albums))

    def fetch_all_albumart(self, songs) -> None:
        """Fetch all albumart"""
        self.art_thread = threading.Thread(
            target=self.connection.execute,
            args=(self.__fetch_all_albumart, songs))
        self.art_thread.start()
    def __fetch_all_albumart(self, cli, songs) -> None:
        self.logger.debug("Fetch all art - start")
        self.art_enabled = True
        for song in songs:
            if self.art_enabled is False:
                break
            try:
                self.__refresh_albumart(
                    cli,
                    song,
                    False)
            except Exception:
                # ignore error and carry on
                pass
        self.logger.debug("Fetch all art - end")

    def refresh_queue(self) -> None:
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

    def refresh_songs(self) -> None:
        """Refresh the songs"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_songs,)).start()
    def __refresh_songs(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_songs()")
        songs = {}
        songs = cli.listallinfo()
        filtered = list(filter(lambda song: song.get('directory', '') == '', songs))
        wx.PostEvent(self.window, MpdSongsEvent(filtered))

    def refresh_playlists(self) -> None:
        """Refresh the playlists"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_playlists,)).start()
    def __refresh_playlists(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("refresh_playlists()")
        playlists = {}
        playlists = cli.listplaylists()
        wx.PostEvent(self.window, MpdPlaylistsEvent(playlists))

    def refresh_albumart(self, song: dict, trigger_event: bool = True) -> None:
        """Refresh the albumart"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__refresh_albumart, song, trigger_event)).start()
    def __refresh_albumart(self, cli: musicpd.MPDClient, song: dict, trigger: bool) -> None:
        self.logger.debug("refresh_albumart()")
        artist = song.get('albumartist', song.get('artist', ''))
        album = song.get('album', '')
        file = song.get('file', '')
        if not self.__albumart_exists(artist, album):
            album_art = {}
            offset = 0
            album_art = {'size':'1','binary':'','data':b''}
            data = b''
            while offset < int(album_art['size']):
                album_art = cli.albumart(file, offset)
                offset += int(album_art['binary'])
                data += album_art['data']
            self.__save_albumart(artist, album, data)
            if trigger:
                wx.PostEvent(self.window, MpdAlbumArtEvent(file))

    def play_queue_pos(self, queue_pos) -> None:
        """Play the queue position"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__play_queue_pos, queue_pos)).start()
    def __play_queue_pos(self, cli: musicpd.MPDClient, queue_pos) -> None:
        self.logger.debug("play_queue_pos()")
        cli.play(queue_pos)
    def delete_queue_pos(self, queue_pos) -> None:
        """Delete the queue position"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__delete_queue_pos, queue_pos)).start()
    def __delete_queue_pos(self, cli: musicpd.MPDClient, queue_pos) -> None:
        self.logger.debug("delete_queue_pos()")
        cli.delete(queue_pos)
    def clear_queue(self) -> None:
        """Clear the queue"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__clear_queue,)).start()
    def __clear_queue(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("clear_queue()")
        cli.clear()

    def search(self, query: str) -> None:
        """Search the database"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__search,query)).start()
    def __search(self, cli: musicpd.MPDClient, query: str) -> None:
        self.logger.debug("search()")
        songs = cli.search(f"(ANY contains \"{query}\")")
        wx.PostEvent(self.window, MpdSearchEvent(songs))

    def play_album_tag(self, album_name: str) -> None:
        """Play the album tag"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__play_album_tag, album_name)).start()
    def __play_album_tag(self, cli: musicpd.MPDClient, album_name: str) -> None:
        self.logger.debug("play_album_tag()")
        cli.clear()
        cli.findadd(f'(Album == "{album_name}")')
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def append_album_tag(self, album_name: str) -> None:
        """Append the album tag"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__append_album_tag, album_name)).start()
    def __append_album_tag(self, cli: musicpd.MPDClient, album_name: str) -> None:
        self.logger.debug("append_album_tag()")
        cli.findadd(f'(Album == "{album_name}")')
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def play_artist_tag(self, artist_name: str) -> None:
        """Play the artist tag"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__play_artist_tag, artist_name)).start()
    def __play_artist_tag(self, cli: musicpd.MPDClient, artist_name: str) -> None:
        self.logger.debug("play_artist_tag()")
        cli.clear()
        cli.findadd(f'(Artist == "{artist_name}")')
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def append_artist_tag(self, artist_name: str) -> None:
        """Append the artist tag"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__append_artist_tag, artist_name)).start()
    def __append_artist_tag(self, cli: musicpd.MPDClient, artist_name: str) -> None:
        self.logger.debug("append_artist_tag()")
        cli.findadd(f'(Artist == "{artist_name}")')
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def play_song(self, file: str) -> None:
        """Play the song"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__play_song, file)).start()
    def __play_song(self, cli: musicpd.MPDClient, file: str) -> None:
        self.logger.debug("play_song()")
        cli.clear()
        cli.add(file)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def save_playlist(self, name: str) -> None:
        """Save the queue as a playlist"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__save_playlist, name)).start()
    def __save_playlist(self, cli: musicpd.MPDClient, name: str) -> None:
        self.logger.debug("save_playlist()")
        cli.save(name)

    def playlist_add(self, name: str, file: str) -> None:
        """Add the file to the playlist"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__playlist_add, name, file)).start()
    def __playlist_add(self, cli: musicpd.MPDClient, name: str, file: str) -> None:
        self.logger.debug("playlist_add()")
        cli.playlistadd(name, file)

    def append_song(self, file: str) -> None:
        """Append the song"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__append_song, file)).start()
    def __append_song(self, cli: musicpd.MPDClient, file: str) -> None:
        self.logger.debug("append_song()")
        cli.add(file)
        queue = cli.playlistid()
        cli.play()
        wx.PostEvent(self.window, MpdQueueEvent(queue)) # do we need this?

    def play_toggle(self) -> None:
        """Play toggle"""
        if self.status.get('state', '') != 'play':
            self.play()
        else:
            self.pause()
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
        """Previous song in queue"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__prev,)).start()
    def __prev(self, cli: musicpd.MPDClient) -> None:
        self.logger.debug("prev()")
        cli.previous()

    def load(self, playlist) -> None:
        """Load playlist"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__load, playlist)).start()
    def __load(self, cli: musicpd.MPDClient, playlist) -> None:
        self.logger.debug("load()")
        cli.load(playlist)

    def remove(self, playlist) -> None:
        """Remove playlist"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__remove, playlist)).start()
    def __remove(self, cli: musicpd.MPDClient, playlist) -> None:
        self.logger.debug("remove()")
        cli.rm(playlist)

    def set_volume(self, volume) -> None:
        """Set volume"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__set_volume, volume)).start()
    def __set_volume(self, cli: musicpd.MPDClient, volume) -> None:
        self.logger.debug("set_volume()")
        cli.setvol(volume)

    def set_repeat(self, repeat) -> None:
        """Set repeat"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__set_repeat, repeat)).start()
    def __set_repeat(self, cli: musicpd.MPDClient, repeat) -> None:
        self.logger.debug("set_repeat()")
        cli.repeat('1' if repeat else '0')

    def set_random(self, random) -> None:
        """Set random"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__set_random, random)).start()
    def __set_random(self, cli: musicpd.MPDClient, random) -> None:
        self.logger.debug("set_random()")
        cli.random('1' if random else '0')

    def set_single(self, single) -> None:
        """Set single"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__set_single, single)).start()
    def __set_single(self, cli: musicpd.MPDClient, single) -> None:
        self.logger.debug("set_single()")
        cli.single('1' if single else '0')

    def set_consume(self, consume) -> None:
        """Set consume"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__set_consume, consume)).start()
    def __set_consume(self, cli: musicpd.MPDClient, consume) -> None:
        self.logger.debug("set_consume()")
        cli.consume(consume)

    def update(self) -> None:
        """Update"""
        threading.Thread(
            target=self.connection.execute,
            args=(self.__update,)).start()
    def __update(self, cli: musicpd.MPDClient):
        self.logger.debug("update()")
        cli.update()

    def __save_albumart(self, artist, album, data):
        """Save album art"""
        ext, typ = self.__get_file_extension(data)
        orig_path = self.__art_path(self.art_folder, self.__art_file(artist, album), ext)
        with open(orig_path, 'w+b') as f:
            f.write(data)
        if typ != wx.BITMAP_TYPE_PNG:
            orig_img = wx.Image(orig_path, type=typ)
            new_path = self.__art_path(self.art_folder, self.__art_file(artist, album), 'png')
            orig_img.SaveFile(new_path, wx.BITMAP_TYPE_PNG)
            os.remove(orig_path)

    def __albumart_exists(self, artist, album):
        """Check if albumart file exists"""
        path = self.__art_path(self.art_folder, self.__art_file(artist, album), 'png')
        return os.path.isfile(path)

    def __get_file_extension(self, data: str) -> None:
        """Get file extension using magic number"""
        if data.startswith(bytes.fromhex('ffd8ffe0')): # jpg, jpeg
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('ffd8ffdb')): # jpg, jpeg
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('ffd8ffe1')): # jpg, jpeg
            return ('jpg', wx.BITMAP_TYPE_JPEG)
        if data.startswith(bytes.fromhex('89504e47')): # png
            return ('png', wx.BITMAP_TYPE_PNG)
        raise Exception(f'Unhandled file type {data[:5]}')

    def __create_art_folder(self, folder) -> None:
        """Create albumart folder"""
        path = os.path.join(os.path.curdir, 'mpdcmd', folder)
        if not os.path.exists(path):
            os.makedirs(path)
    def __art_path(self, folder, file, ext) -> str:
        """Get the albumart path"""
        return os.path.join(os.path.curdir, 'mpdcmd', folder, f"{file}.{ext}")
    def __art_file(self, artist, album) -> str:
        """Get the art file name"""
        # lazy fix for invalid filename characters
        return base64.urlsafe_b64encode(f'{artist}-{album}'.encode())
    def get_default_albumart(self) -> wx.Bitmap:
        """Get the default albumart"""
        path = self.__art_path('icons', 'icon', 'png')
        return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()

    def get_albumart(self, song) -> wx.Bitmap:
        """Get the albumart"""
        artist = song.get('albumartist', song.get('artist', ''))
        album = song.get('album', '')
        path = self.__art_path(self.art_folder, self.__art_file(artist, album), 'png')
        if os.path.isfile(path):
            return wx.Image(path, type=wx.BITMAP_TYPE_PNG).Scale(80, 80).ConvertToBitmap()
        return self.get_default_albumart()

class MpdIdleThread(threading.Thread):
    """Thread to check the idle updates"""

    def __init__(self, controller: MpdController):
        """Initialise the MpdIdleThread"""
        threading.Thread.__init__(self)
        self.controller = controller

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.actions = {
            'player': self.__action_player,
            'mixer': self.__action_mixer,
            'playlist': self.__action_playlist,
            'update': self.__action_update,
            'database': self.__action_database,
            'options': self.__action_options,
            'stored_playlist': self.__action_stored_playlist,
        }
        self.running = False
        self.socket_timeout = 10

    def run(self):
        """Start the thread (override)"""
        self.running = True
        while self.running:
            self.logger.debug("tick()")
            self.controller.connection.execute(self.__idle)
    def stop(self) -> None:
        """Stop the thread"""
        self.running = False

    def __idle(self, cli: musicpd.MPDClient) -> None:
        """Refresh the status info"""
        self.logger.debug("idle()")
        cli.socket_timeout = self.socket_timeout
        try:
            self.logger.debug('Starting idle')
            idles = cli.idle()
            self.logger.debug('Idle response %s', idles)
            for idle in idles:
                if idle in self.actions:
                    self.actions[idle]()
                else:
                    self.logger.warning('Unhandled idle response %s', idle)
        except TimeoutError:
            self.logger.debug('Idle timeout after %ds', self.socket_timeout)

    def __action_player(self):
        """Player idle action"""
        # start/stop/seek or changed tags of current song
        self.logger.debug('Player action')
        wx.PostEvent(self.controller.window, MpdIdlePlayerEvent())

    def __action_mixer(self):
        """Mixer idle action"""
        # volume has been changed
        self.logger.debug('Mixer action')
        wx.PostEvent(self.controller.window, MpdIdleMixerEvent())

    def __action_playlist(self):
        """Playlists idle action"""
        # queue has been modified
        self.logger.debug('Playlist action')
        wx.PostEvent(self.controller.window, MpdIdlePlaylistEvent())

    def __action_update(self):
        """Update idle action"""
        # update has started or finished
        self.logger.debug('Update action')
        wx.PostEvent(self.controller.window, MpdIdleUpdateEvent())

    def __action_database(self):
        """Database idle action"""
        # database was modified
        self.logger.debug('Database action')
        wx.PostEvent(self.controller.window, MpdIdleDatabaseEvent())

    def __action_options(self):
        """Options idle action"""
        # option was modified
        self.logger.debug('Options action')
        wx.PostEvent(self.controller.window, MpdIdleOptionsEvent())
    
    def __action_stored_playlist(self):
        """Stored playlist idle action"""
        # playlist was stored
        self.logger.debug("Stored playlist action")
        wx.PostEvent(self.controller.window, MpdIdleStoredPlaylistEvent())

class MpdCmdFrame(wx.Frame):
    """The main frame for the MpdCmd application"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-instance-attributes
    def __init__(self, *args, **kw):
        """Initialise MpdCmdFrame"""
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        # init mpd
        self.mpd = MpdController(self)

        self.kbd_thread = None
        
        self.preferences_file = os.path.join(os.path.curdir, 'preferences.json')
        self.preferences = self.__load_preferences()
        self.__process_preferences()

        self.Bind(EVT_MPD_CONNECTION, self.on_connection_changed)
        self.Bind(EVT_MPD_STATS, self.on_stats_changed)
        self.Bind(EVT_MPD_STATUS, self.on_status_changed)
        self.Bind(EVT_MPD_SONGS, self.on_songs_changed)
        self.Bind(EVT_MPD_PLAYLISTS, self.on_playlists_changed)
        self.Bind(EVT_MPD_ALBUMART, self.on_albumart_changed)
        self.Bind(EVT_MPD_SEARCH, self.on_search_results)

        self.Bind(EVT_MPD_CTRL_CURRENTSONG, self.on_current_song_changed)
        self.Bind(EVT_MPD_CTRL_ALBUMS, self.on_albums_changed)
        self.Bind(EVT_MPD_CTRL_QUEUE, self.on_queue_changed)

        self.Bind(EVT_MPD_IDLE_PLAYER, self.on_idle_player)
        self.Bind(EVT_MPD_IDLE_MIXER, self.on_idle_mixer)
        self.Bind(EVT_MPD_IDLE_PLAYLIST, self.on_idle_playlist)
        self.Bind(EVT_MPD_IDLE_UPDATE, self.on_idle_update)
        self.Bind(EVT_MPD_IDLE_DATABASE, self.on_idle_database)
        self.Bind(EVT_MPD_IDLE_OPTIONS, self.on_idle_options)
        self.Bind(EVT_MPD_IDLE_STOREDPLAYLIST, self.on_idle_storedplaylist)

        # init properties
        self.status = {}
        self.current_song = {}
        self.playlists = []
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

        if SHOW_POSITION_SLIDER:
            self.current_song_pos = wx.Slider(self.l_panel, minValue=0, maxValue=1)
            self.l_sizer.Add(self.current_song_pos, 0, wx.EXPAND|wx.ALL, 1)

        tr = self.make_transport(self.l_panel)
        self.l_sizer.Add(tr, 0, wx.ALL|wx.ALL, 1)

        bitmap = self.mpd.get_default_albumart()
        # TODO: better solution to keep art square?
        self.art = wx.StaticBitmap(self.r_panel, wx.ID_ANY, bitmap, size=(80,80))
        self.r_sizer.Add(self.art, 0, wx.EXPAND|wx.ALL, 1)

        self.logger.info("Initialising UI")

        self.notification = None

        self.make_menu_bar()
        self.CreateStatusBar()

        self.update_status()
        self.update_statusbar_text()
        self.update_current_song_time()

        self.mpd.start()
        self.timer.Start(1000, wx.TIMER_CONTINUOUS)

    def __process_preferences(self):
        if self.kbd_thread:
            self.kbd_thread.stop()
        if self.preferences.get('mediakeys', DEFAULT_OPTION_MEDIAKEYS):
            self.logger.warning("Keyboard listener (pynput) enabled")
            self.kbd_thread = Listener(on_press=self.__key_press, on_release=None)
            self.kbd_thread.start()    
        self.mpd.connection = MpdConnection(self, self.preferences)
        self.refresh()

    def __key_press(self, key) -> None:
        if key == Key.media_play_pause:
            self.on_play_toggle(None)
        if key == Key.media_next:
            self.next_button_click(None)
        if key == Key.media_previous:
            self.prev_button_click(None)
        if key == Key.media_volume_up:
            self.current_vol.SetValue(self.current_vol.GetValue()+5)
            self.vol_scroll_changed(None)
        if key == Key.media_volume_down:
            self.current_vol.SetValue(self.current_vol.GetValue()-5)
            self.vol_scroll_changed(None)

    def refresh(self):
        """Refresh"""
        self.logger.info("Refreshing MPD data")
        self.mpd.refresh_stats()
        self.mpd.refresh_status()
        self.mpd.refresh_albums()
        self.mpd.refresh_queue()
        self.mpd.refresh_playlists()
        self.mpd.refresh_songs()

    def __load_preferences(self):
        """Load preferences"""
        if os.path.isfile(self.preferences_file) is False:
            with open(self.preferences_file, 'w', encoding='utf-8') as file:
                preferences = {
                    "host":"",
                    "port":"",
                    "username":"",
                    "password":"",
                    "notifications":DEFAULT_OPTION_NOTIFICATIONS,
                    "mediakeys":DEFAULT_OPTION_MEDIAKEYS,
                    "fetchallart":DEFAULT_OPTION_FETCHALLART}
                file.write(json.dumps(preferences))
        with open(self.preferences_file, 'r', encoding='utf-8') as f:
            return json.loads(f.read())
    def __save_preferences(self):
        """Save preferences"""
        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.preferences))

    def make_notebook(self, parent) -> wx.Notebook:
        """Make the notebook"""
        notebook = wx.Notebook(parent)

        self.queue_ctrl = self.__make_queue_ctrl(notebook)
        notebook.AddPage(self.queue_ctrl, "Queue")

        self.album_ctrl = self.__make_albums_ctrl(notebook)
        notebook.AddPage(self.album_ctrl, "Albums")

        self.playlists_ctrl = self.__make_playlists_ctrl(notebook)
        notebook.AddPage(self.playlists_ctrl, "Playlists")

        self.songs_ctrl = self.__make_songs_ctrl(notebook)
        notebook.AddPage(self.songs_ctrl, "Songs")

        search_page = self.__make_search_ctrl(notebook)
        notebook.AddPage(search_page, "Search")

        return notebook
    def __make_queue_ctrl(self, parent: wx.Window) -> wx.ListCtrl:
        """Make the queue control"""
        queue_ctrl = wx.ListCtrl(parent)
        queue_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        queue_ctrl.InsertColumn(0, "", width=20)
        queue_ctrl.InsertColumn(1, "Id", width=50)
        queue_ctrl.InsertColumn(2, "Position", width=70)
        queue_ctrl.InsertColumn(3, "Album", width=150)
        queue_ctrl.InsertColumn(4, "Artist", width=100)
        queue_ctrl.InsertColumn(5, "Track", width=50)
        queue_ctrl.InsertColumn(6, "Title", width=200)
        queue_ctrl.InsertColumn(7, "Duration", width=70)
        try:
            queue_ctrl.SetColumnsOrder([0,1,2,3,4,5,6,7])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.queue_item_activated, queue_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.queue_context_menu, queue_ctrl)
        return queue_ctrl
    def __make_albums_ctrl(self, parent: wx.Window) -> wx.ListCtrl:
        """Make the albums control"""
        album_ctrl = wx.ListCtrl(parent)
        album_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        album_ctrl.InsertColumn(0, "", width=20)
        album_ctrl.InsertColumn(1, "Album", width=150)
        album_ctrl.InsertColumn(2, "Artist", width=100)
        album_ctrl.InsertColumn(3, "Tracks", width=50)
        album_ctrl.InsertColumn(4, "Duration", width=50)
        try:
            album_ctrl.SetColumnsOrder([0,1,2,3,4])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.album_item_activated, album_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.albums_context_menu, album_ctrl)
        return album_ctrl
    def __make_playlists_ctrl(self, parent: wx.Window) -> wx.ListCtrl:
        """Make the playlists control"""
        playlists_ctrl = wx.ListCtrl(parent)
        playlists_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        playlists_ctrl.InsertColumn(0, "Playlist", width=100)
        playlists_ctrl.InsertColumn(1, "Last modified", width=100)
        try:
            playlists_ctrl.SetColumnsOrder([0,1])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.playlists_item_activated, playlists_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.playlists_context_menu, playlists_ctrl)
        return playlists_ctrl
    def __make_songs_ctrl(self, parent: wx.Window) -> wx.ListCtrl:
        """Make the songs control"""
        songs_ctrl = wx.ListCtrl(parent)
        songs_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        songs_ctrl.InsertColumn(0, "", width=20)
        songs_ctrl.InsertColumn(1, "Album", width=150)
        songs_ctrl.InsertColumn(2, "Artist", width=100)
        songs_ctrl.InsertColumn(3, "Track", width=50)
        songs_ctrl.InsertColumn(4, "Title", width=200)
        songs_ctrl.InsertColumn(5, "Duration", width=70)
        songs_ctrl.InsertColumn(6, "File", width=70)
        try:
            songs_ctrl.SetColumnsOrder([0,1,2,3,4,5,6])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.song_item_activated, songs_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.songs_context_menu, songs_ctrl)
        return songs_ctrl
    def __make_search_ctrl(self, parent: wx.Window) -> wx.Panel:
        """Make the search control"""
        result_panel = wx.Panel(parent)
        #result_panel.SetBackgroundColour((0x00, 0xff, 0xff))
        result_sizer = wx.BoxSizer(wx.VERTICAL)

        search_panel = wx.Panel(result_panel)
        #search_panel.SetBackgroundColour((0xff, 0xff, 0x00))
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        search_label = wx.StaticText(search_panel, label='Search')
        search_sizer.Add(search_label, 0, wx.EXPAND|wx.ALL, 1)
        self.search_box = wx.TextCtrl(search_panel, value='')
        search_sizer.Add(self.search_box, 0, wx.EXPAND|wx.ALL, 1)
        search_button = wx.Button(search_panel, label="Search")
        self.Bind(wx.EVT_BUTTON, self.on_search, search_button)
        search_sizer.Add(search_button, 0, wx.EXPAND|wx.ALL, 1)
        search_panel.SetSizer(search_sizer)

        self.search_ctrl = wx.ListCtrl(result_panel)
        self.search_ctrl.SetWindowStyleFlag(wx.LC_REPORT)
        self.search_ctrl.InsertColumn(0, "", width=20)
        self.search_ctrl.InsertColumn(1, "Album", width=150)
        self.search_ctrl.InsertColumn(2, "Artist", width=100)
        self.search_ctrl.InsertColumn(3, "Track", width=50)
        self.search_ctrl.InsertColumn(4, "Title", width=200)
        self.search_ctrl.InsertColumn(5, "Duration", width=70)
        self.search_ctrl.InsertColumn(6, "File", width=70)
        try:
            self.search_ctrl.SetColumnsOrder([0,1,2,3,4,5,6])
        except NotImplementedError:
            pass
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.search_item_activated, self.search_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.search_context_menu, self.search_ctrl)

        result_sizer.Add(search_panel, 0, wx.EXPAND|wx.ALL, 1)
        result_sizer.Add(self.search_ctrl, 1, wx.EXPAND|wx.ALL, 1)
        result_panel.SetSizer(result_sizer)

        return result_panel

    def make_transport(self, parent) -> wx.Panel:
        """Make the transport"""
        transport = wx.Panel(parent)
        tr_hori = wx.BoxSizer(wx.HORIZONTAL)

        prev_button = wx.Button(transport, label="Prev")
        self.Bind(
            wx.EVT_BUTTON, self.prev_button_click, prev_button)
        tr_hori.Add(prev_button, 0, wx.EXPAND|wx.ALL, 1)

        self.play_button = wx.Button(transport, label="")
        self.Bind(
            wx.EVT_BUTTON, self.on_play_toggle, self.play_button)
        tr_hori.Add(self.play_button, 0, wx.EXPAND|wx.ALL, 1)

        next_button = wx.Button(transport, label="Next")
        self.Bind(
            wx.EVT_BUTTON, self.next_button_click, next_button)
        tr_hori.Add(next_button, 0, wx.EXPAND|wx.ALL, 1)

        self.current_vol = wx.Slider(transport, minValue=0, maxValue=100, style=wx.SL_VALUE_LABEL)
        self.Bind(
            wx.EVT_SCROLL_CHANGED, self.vol_scroll_changed, self.current_vol)
        self.Bind(
            wx.EVT_COMMAND_SCROLL_THUMBTRACK, self.vol_scroll_thumbtrack, self.current_vol)
        self.Bind(
            wx.EVT_COMMAND_SCROLL_THUMBRELEASE, self.vol_scroll_thumbrelease, self.current_vol)
        tr_hori.Add(self.current_vol, 0, wx.EXPAND|wx.ALL, 1)

        self.repeat_check = wx.CheckBox(transport, label="Rpt")
        self.repeat_check.SetValue(False)
        self.Bind(
            wx.EVT_CHECKBOX, self.on_repeat_changed, self.repeat_check)
        tr_hori.Add(self.repeat_check, 0, wx.EXPAND|wx.ALL, 1)

        self.random_check = wx.CheckBox(transport, label="Rnd")
        self.random_check.SetValue(False)
        self.Bind(
            wx.EVT_CHECKBOX, self.on_random_changed, self.random_check)
        tr_hori.Add(self.random_check, 0, wx.EXPAND|wx.ALL, 1)

        self.single_check = wx.CheckBox(transport, label="Sgl")
        self.single_check.SetValue(False)
        self.Bind(
            wx.EVT_CHECKBOX, self.on_single_changed, self.single_check)
        tr_hori.Add(self.single_check, 0, wx.EXPAND|wx.ALL, 1)

        self.consume_check = wx.CheckBox(transport, label='Cns')
        self.consume_check.SetValue(False)
        self.Bind(
            wx.EVT_CHECKBOX, self.on_consume_changed, self.consume_check)
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
        refresh_item = server_menu.Append(-1, "&Refresh from server", "Refresh from server")
        update_item = server_menu.Append(-1, "Trigger a server &Update", "Trigger a server update")

        queue_menu = wx.Menu()
        save_item = queue_menu.Append(-1, "&Save queue as playlist", "Save queue as playlist")
        clear_item = queue_menu.Append(-1, "&Clear queue", "Clear queue")

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT)

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(server_menu, "&Server")
        menu_bar.Append(queue_menu, "&Queue")
        menu_bar.Append(help_menu, "&Help")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.on_menu_pref, pref_item)
        self.Bind(wx.EVT_MENU, self.on_menu_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_menu_refresh, refresh_item)
        self.Bind(wx.EVT_MENU, self.on_menu_update, update_item)
        self.Bind(wx.EVT_MENU, self.on_menu_save, save_item)
        self.Bind(wx.EVT_MENU, self.on_menu_clear, clear_item)
        self.Bind(wx.EVT_MENU, self.on_menu_about, about_item)

    def seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to time"""
        return "%02d:%02d" % (seconds//60, seconds%60) # pylint: disable=consider-using-f-string

    def on_tick(self, _event: wx.TimerEvent) -> None:
        """On timer tick"""
        self.logger.debug("on_tick")
        if self.playing:
            self.elapsed += 1
        self.update_current_song_time()

    def on_connection_changed(self, event: MpdConnectionEvent) -> None:
        """MPD connection changed"""
        self.connection_status = event.get_value()
        self.logger.info("Connection changed %s", self.connection_status)
        self.update_statusbar_text()
    def on_stats_changed(self, event: MpdStatsEvent) -> None:
        """MPD stats changed"""
        stats = event.get_value()
        self.logger.info("Stats changed %s", stats)
        self.update_title(stats)
    def on_status_changed(self, event: MpdStatusEvent) -> None:
        """MPD status changed"""
        self.status = event.get_value()
        self.logger.info("Status changed %s", self.status)
        self.update_status()
        self.mpd.refresh_current_song()
    def on_songs_changed(self, event: MpdSongsEvent) -> None:
        """MPD songs changed"""
        songs = event.get_value()
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
        if self.preferences.get('fetchallart', DEFAULT_OPTION_FETCHALLART):
            self.mpd.fetch_all_albumart(songs)
    def on_playlists_changed(self, event: MpdPlaylistsEvent) -> None:
        """MPD playlists changed"""
        self.playlists = event.get_value()
        self.logger.info("Playlists changed %s", self.playlists)
        self.playlists_ctrl.DeleteAllItems()
        for playlist in self.playlists:
            self.playlists_ctrl.Append([
                playlist['playlist'],
                playlist['last-modified']])
    def on_albumart_changed(self, event: MpdAlbumArtEvent) -> None:
        """MPD albumart changed"""
        songid = event.get_value()
        self.logger.info("Albumart changed %s", songid)
        self.set_current_albumart()
    def on_search_results(self, event: MpdSearchEvent) -> None:
        """MPD search results"""
        results = event.get_value()
        self.logger.info("Search results %s", len(results))
        self.search_ctrl.DeleteAllItems()
        for song in results:
            prefix = ''
            self.search_ctrl.Append([
                prefix,
                song.get('album', ''),
                song.get('artist', ''),
                song.get('track', ''),
                song.get('title', ''),
                self.seconds_to_time(float(song.get('duration', ''))),
                song.get('file', '')])

    def queue_context_menu(self, event):
        """Queue context menu"""
        self.logger.debug("queue_context_menu()")
        menu = wx.Menu()
        clear_item = menu.Append(-1, "Clear")
        self.Bind(wx.EVT_MENU, self.on_menu_queue_clear, clear_item)
        menu.AppendSeparator()
        delete_item = menu.Append(-1, "Delete")
        self.Bind(wx.EVT_MENU, self.on_menu_queue_delete, delete_item)
        menu.AppendSeparator()
        play_item = menu.Append(-1, "Play")
        self.Bind(wx.EVT_MENU, self.on_menu_queue_play, play_item)
        self.PopupMenu(menu, event.GetPoint())
    def albums_context_menu(self, event):
        """Albums context menu"""
        self.logger.debug("albums_context_menu()")
        menu = wx.Menu()
        append_item = menu.Append(-1, "Append Album")
        self.Bind(wx.EVT_MENU, self.on_menu_albums_append_album, append_item)
        play_item = menu.Append(-1, "Play Album")
        self.Bind(wx.EVT_MENU, self.on_menu_albums_play_album, play_item)
        menu.AppendSeparator()
        append_artist_item = menu.Append(-1, "Append Artist")
        self.Bind(wx.EVT_MENU, self.on_menu_albums_append_artist, append_artist_item)
        play_artist_item = menu.Append(-1, "Play Artist")
        self.Bind(wx.EVT_MENU, self.on_menu_albums_play_artist, play_artist_item)
        self.PopupMenu(menu, event.GetPoint())
    def playlists_context_menu(self, event):
        """Playlists context menu"""
        self.logger.debug("playlists_context_menu()")
        menu = wx.Menu()
        load_item = menu.Append(-1, "Load")
        self.Bind(wx.EVT_MENU, self.on_menu_playlist_load, load_item)
        remove_item = menu.Append(-1, "Remove")
        self.Bind(wx.EVT_MENU, self.on_menu_playlist_remove, remove_item)
        self.PopupMenu(menu, event.GetPoint())
    def songs_context_menu(self, event):
        """Songs context menu"""
        self.logger.debug("songs_context_menu()")
        menu = wx.Menu()
        append_item = menu.Append(-1, "Append Song")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_append_song, append_item)
        play_item = menu.Append(-1, "Play Song")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_play_song, play_item)
        menu.AppendSeparator()
        append_album_item = menu.Append(-1, "Append Album")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_append_album, append_album_item)
        play_album_item = menu.Append(-1, "Play Album")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_play_album, play_album_item)
        menu.AppendSeparator()
        append_artist_item = menu.Append(-1, "Append Artist")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_append_artist, append_artist_item)
        play_artist_item = menu.Append(-1, "Play Artist")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_play_artist, play_artist_item)

        menu.AppendSeparator()
        append_menu = wx.Menu()
        append_new_item = append_menu.Append(-1, "New")
        self.Bind(wx.EVT_MENU, self.on_menu_songs_append_newplaylist, append_new_item)
        append_menu.AppendSeparator()
        for playlist in self.playlists:
            pl_item = append_menu.Append(-1, playlist['playlist'])
            self.Bind(wx.EVT_MENU, lambda event: self.on_menu_songs_append_playlist(playlist['playlist'], event), pl_item)
        menu.AppendSubMenu(append_menu, "Append To Playlist")
        
        self.PopupMenu(menu, event.GetPoint())
    def search_context_menu(self, event):
        """Search context menu"""
        self.logger.debug("search_context_menu()")
        menu = wx.Menu()
        append_item = menu.Append(-1, "Append Song")
        self.Bind(wx.EVT_MENU, self.on_menu_search_append_song, append_item)
        play_item = menu.Append(-1, "Play Song")
        self.Bind(wx.EVT_MENU, self.on_menu_search_play_song, play_item)
        menu.AppendSeparator()
        append_album_item = menu.Append(-1, "Append Album")
        self.Bind(wx.EVT_MENU, self.on_menu_search_append_album, append_album_item)
        play_album_item = menu.Append(-1, "Play Album")
        self.Bind(wx.EVT_MENU, self.on_menu_search_play_album, play_album_item)
        menu.AppendSeparator()
        append_artist_item = menu.Append(-1, "Append Artist")
        self.Bind(wx.EVT_MENU, self.on_menu_search_append_artist, append_artist_item)
        play_artist_item = menu.Append(-1, "Play Artist")
        self.Bind(wx.EVT_MENU, self.on_menu_search_play_artist, play_artist_item)

        menu.AppendSeparator()
        append_menu = wx.Menu()
        append_new_item = append_menu.Append(-1, "New")
        self.Bind(wx.EVT_MENU, self.on_menu_search_append_newplaylist, append_new_item)
        append_menu.AppendSeparator()
        for playlist in self.playlists:
            pl_item = append_menu.Append(-1, playlist['playlist'])
            self.Bind(wx.EVT_MENU, lambda event: self.on_menu_search_append_playlist(playlist['playlist'], event), pl_item)
        menu.AppendSubMenu(append_menu, "Append To Playlist")
        
        self.PopupMenu(menu, event.GetPoint())

    def on_current_song_changed(self, event: MpdCurrentSongEvent) -> None:
        """MPD current song changed"""
        self.current_song = event.get_value()
        self.logger.info("Song changed %s", self.current_song)
        self.mpd.refresh_albumart(self.current_song)
        self.update_current_song()
    def on_albums_changed(self, event: MpdAlbumsEvent) -> None:
        """Albums changed"""
        albums = event.get_value()
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
        queue = event.get_value()
        self.logger.info("Queue changed %s", len(queue))
        self.queue_ctrl.DeleteAllItems()
        for idx,song in enumerate(queue):
            prefix = ''
            if self.current_song.get('pos', '') == str(idx):
                prefix = '>'
            track = song.get('track', None)
            artist = song.get('artist', None)
            title = song.get('title', None)
            album = song.get('album', None)
            name = song.get('name', None)
            self.queue_ctrl.Append([
                prefix,
                song['id'],
                song['pos'],
                album,
                artist,
                track,
                title,
                self.seconds_to_time(float(song.get('duration', '0')))])

    def on_idle_player(self, _event: MpdIdlePlayerEvent) -> None:
        """Idle player event"""
        self.logger.debug("Idle player")
        self.mpd.refresh_status()
    def on_idle_mixer(self, _event: MpdIdleMixerEvent) -> None:
        """Idle mixer event"""
        self.logger.debug("Idle mixer")
        self.mpd.refresh_status()
    def on_idle_playlist(self, _event: MpdIdlePlaylistEvent) -> None:
        """Idle playlist event"""
        self.logger.debug("Idle playlist")
        self.mpd.refresh_queue()
    def on_idle_update(self, _event: MpdIdleUpdateEvent) -> None:
        """Idle update event"""
        self.logger.debug("Idle update")
    def on_idle_database(self, _event: MpdIdleDatabaseEvent) -> None:
        """Idle database event"""
        self.logger.debug("Idle database")
        # TODO: refresh albums and songs?
    def on_idle_options(self, _event: MpdIdleOptionsEvent) -> None:
        """Idle options event"""
        self.logger.debug("Idle options")
        self.mpd.refresh_status()
    def on_idle_storedplaylist(self, _event: MpdIdleStoredPlaylistEvent) -> None:
        """Idle stored_playlist event"""
        self.logger.debug("Idle stored_playlist")
        self.mpd.refresh_playlists()

    def album_item_activated(self, _event: wx.ListEvent) -> None:
        """Album item selected"""
        album_name = self.album_ctrl.GetItem(
            self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Album selected %s", album_name)
        self.mpd.play_album_tag(album_name)
    def queue_item_activated(self, _event: wx.ListEvent) -> None:
        """Queue item selected"""
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item selected %s", queue_pos)
        self.mpd.play_queue_pos(queue_pos)
    def playlists_item_activated(self, _event: wx.ListEvent):
        """Playlist item selected"""
        playlist = self.playlists_ctrl.GetItem(
            self.playlists_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Playlist selected %s", playlist)
        self.mpd.load(playlist)
    def song_item_activated(self, _event: wx.ListEvent):
        """Song item selected"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Song selected %s", song)
    def search_item_activated(self, _event: wx.ListEvent):
        """Search item selected"""
        song = self.search_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.debug("Search selected %s", song)

    def update_title(self, stats: dict) -> None:
        """Update the title text"""
        # pylint: disable=consider-using-f-string
        # pylint: disable=invalid-name
        self.Title = "MPDCMD [Artists %s Albums %s Songs %s]" % (
            stats.get('artists', '?'),
            stats.get('albums', '?'),
            stats.get('songs', '?'))
    def update_status(self) -> None:
        """Update status related ui"""
        self.update_play_pause()
        self.update_volume()
        self.update_options()
        self.update_song_time()
    def update_play_pause(self) -> None:
        """Update play/pause button label"""
        if self.status.get('state', '') != 'play':
            self.play_button.SetLabel("Play")
            self.playing = False
        else:
            self.play_button.SetLabel("Pause")
            self.playing = True
    def update_volume(self) -> None:
        """Update the volume slider value"""
        if not self.volume_changing:
            self.current_vol.SetValue(int(self.status.get('volume', '0')))
    def update_options(self) -> None:
        """Update the options ui"""
        self.repeat_check.SetValue(bool(self.status.get('repeat', '0') == '1'))
        self.random_check.SetValue(bool(self.status.get('random', '0') == '1'))
        self.single_check.SetValue(bool(self.status.get('repeat', '0') == '1'))
        self.consume_check.SetValue(bool(self.status.get('consume', '0') == '1'))
    def update_song_time(self) -> None:
        """Update song time"""
        self.elapsed = float(self.status.get('elapsed', '0'))
        self.duration = float(self.status.get('duration', '0'))
        self.update_current_song_time()
    def update_current_song(self) -> None:
        """Update current song"""
        for s in range(0, self.queue_ctrl.GetItemCount()):
            pos = self.queue_ctrl.GetItem(s, col=2).GetText()
            if self.current_song.get('pos', '') == str(pos):
                self.queue_ctrl.SetItem(s, 0, '>')
            else:
                self.queue_ctrl.SetItem(s, 0, ' ')
        self.show_notification()
        self.set_current_albumart()
        track = self.current_song.get('track', None)
        artist = self.current_song.get('artist', None)
        title = self.current_song.get('title', None)
        album = self.current_song.get('album', None)
        name = self.current_song.get('name', None)
        if track and artist and title and album:
            # music file
            # pylint: disable=consider-using-f-string
            self.current_song_text.SetLabel("%s. %s - %s (%s)" % (
                track,
                artist,
                title,
                album))
        if name:
            # music stream (title can be empty)
            self.current_song_text.SetLabel("%s (%s)" % (
                title,
                name))
        self.update_statusbar_text()
    def show_notification(self) -> None:
        """Show notification"""
        if self.preferences.get('notifications', True):
            track = self.current_song.get('track', None)
            artist = self.current_song.get('artist', None)
            title = self.current_song.get('title', None)
            album = self.current_song.get('album', None)
            name = self.current_song.get('name', None)
            if self.notification != None:
                self.notification.Close()
                self.notification = None
            if track and artist and title and album:
                # music file
                # pylint: disable=consider-using-f-string
                self.notification = wx.adv.NotificationMessage(
                    "MPDCMD", "%s. %s - %s\r\n%s" % (
                        self.current_song.get('track', '?'),
                        self.current_song.get('artist', '?'),
                        self.current_song.get('title', '?'),
                        self.current_song.get('album', '?')))
            if name:
                # music stream (title can be empty)
                self.notification = wx.adv.NotificationMessage(
                    "MPDCMD", "%s\r\n%s" % (
                        self.current_song.get('name', '?'),
                        self.current_song.get('title', '?')))
            if self.notification:
                bitmap = self.mpd.get_albumart(self.current_song)
                self.notification.SetIcon(wx.Icon(bitmap))
                self.notification.Show(5)
    def set_current_albumart(self) -> None:
        """Set the album art image for the currently playing song"""
        bitmap = self.mpd.get_albumart(self.current_song)
        self.art.Bitmap = bitmap

    def update_statusbar_text(self) -> None:
        """Update status bar text"""
        # pylint: disable=consider-using-f-string
        self.SetStatusText("%s %s | %s:%s %s" % (
            self.current_song.get('file', 'FILE'),
            self.current_song.get('format', 'FORMAT'),
            self.preferences.get('host', ''),
            self.preferences.get('port', ''),
            self.connection_status))
    def update_current_song_time(self):
        """Update current song time text"""
        elapsed = self.seconds_to_time(self.elapsed)
        duration = self.seconds_to_time(self.duration)
        self.current_song_time.SetLabel(f"{elapsed}/{duration}")
        if SHOW_POSITION_SLIDER:
            self.current_song_pos.SetMax(int(self.duration))
            self.current_song_pos.SetValue(int(self.elapsed))

    def on_play_toggle(self, _event: wx.CommandEvent) -> None:
        """Play/pause clicked"""
        self.logger.debug("on_play_toggle()")
        self.mpd.play_toggle()
    def next_button_click(self, _event: wx.CommandEvent) -> None:
        """Next clicked"""
        self.logger.debug("next_button_click()")
        self.mpd.next()
    def prev_button_click(self, _event: wx.CommandEvent) -> None:
        """Previous clicked"""
        self.logger.debug("prev_button_click()")
        self.mpd.prev()
    def vol_scroll_changed(self, _event: wx.CommandEvent) -> None:
        """Volume slider changed"""
        vol = self.current_vol.GetValue()
        self.mpd.set_volume(int(vol))
    def vol_scroll_thumbtrack(self, _event) -> None:
        """Volume scroll started"""
        self.volume_changing = True
    def vol_scroll_thumbrelease(self, _event) -> None:
        """Volume scroll stopped"""
        self.volume_changing = False
    def on_repeat_changed(self, _event) -> None:
        """Repeat checkbox changed"""
        repeat = self.repeat_check.GetValue()
        self.mpd.set_repeat(repeat)
    def on_random_changed(self, _event) -> None:
        """Random checkbox changed"""
        random = self.random_check.GetValue()
        self.mpd.set_random(random)
    def on_single_changed(self, _event) -> None:
        """Single checkbox changed"""
        single = self.single_check.GetValue()
        self.mpd.set_single(single)
    def on_consume_changed(self, _event) -> None:
        """Consume checkbox changed"""
        consume = self.consume_check.GetValue()
        self.mpd.set_consume(consume)
    def on_search(self, event) -> None:
        """Do a search"""
        query = self.search_box.Value
        self.mpd.search(query)

    def on_menu_pref(self, _event: wx.CommandEvent) -> None:
        """Preferences menu selected"""
        self.logger.debug("on_menu_pref()")
        preferences = MpdPreferencesFrame(
            self.preferences,
            self,
            title='Preferences',
            size=(320,340))
        if preferences.ShowModal() == wx.ID_SAVE:
            self.preferences = preferences.preferences
            self.__save_preferences()
            self.__process_preferences()

    def on_menu_save(self, _event: wx.CommandEvent) -> None:
        """Save queue as playlist"""
        self.logger.debug("on_menu_save()")
        save = MpdSavePlaylistFrame(
            self,
            title='Save',
            size=(320,140))
        save.Show()
    def on_menu_clear(self, _event: wx.CommandEvent) -> None:
        """Clear menu selected"""
        self.logger.debug("on_menu_clear()")
        self.mpd.clear_queue()
    def on_menu_about(self, _event: wx.CommandEvent) -> None:
        """About menu selected"""
        self.logger.debug("on_menu_about()")
        wx.MessageBox(
            "Music Player Daemon Command\r\nWxPython MPD Client",
            "About",
            wx.OK|wx.ICON_INFORMATION)
    def on_menu_refresh(self, _event: wx.CommandEvent) -> None:
        """Refresh menu selected"""
        self.logger.debug("on_menu_refresh()")
        self.refresh()
    def on_menu_update(self, _event: wx.CommandEvent) -> None:
        """Update menu selected"""
        self.logger.debug("on_menu_update()")
        self.mpd.update()
        wx.MessageBox("Update triggered", "Update", wx.OK|wx.ICON_INFORMATION)
    def on_menu_exit(self, _event: wx.CommandEvent) -> None:
        """Exit menu selected"""
        self.logger.debug("OMenuExit()")
        self.Close(True)
    def on_close(self, _event: wx.CommandEvent) -> None:
        """On window/frame close"""
        self.logger.debug("on_close()")
        if self.mpd:
            self.mpd.stop()
        if self.kbd_thread:
            self.kbd_thread.stop()
        self.timer.Stop()
        self.Destroy()

    def on_menu_queue_clear(self, _event: wx.CommandEvent) -> None:
        """Menu Queue Clear"""
        self.logger.info("Queue clear")
        self.mpd.clear_queue()
    def on_menu_queue_delete(self, _event: wx.CommandEvent) -> None:
        """Menu Queue Delete"""
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item delete %s", queue_pos)
        self.mpd.delete_queue_pos(queue_pos)
    def on_menu_queue_play(self, _event: wx.CommandEvent) -> None:
        """Menu Queue Play"""
        queue_pos = self.queue_ctrl.GetItem(
            self.queue_ctrl.GetFirstSelected(), col=2).GetText()
        queue_pos = int(queue_pos)
        self.logger.info("Queue item play %s", queue_pos)
        self.mpd.play_queue_pos(queue_pos)

    def on_menu_albums_append_album(self, _event) -> None:
        """Albums append album"""
        album_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Albums item append %s", album_name)
        self.mpd.append_album_tag(album_name)
    def on_menu_albums_play_album(self, _event) -> None:
        """Albums play album"""
        album_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.info("Albums item play %s", album_name)
        self.mpd.play_album_tag(album_name)
    def on_menu_albums_append_artist(self, _event) -> None:
        """Albums append artist"""
        artist_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.info("Albums item append %s", artist_name)
        self.mpd.append_artist_tag(artist_name)
    def on_menu_albums_play_artist(self, _event) -> None:
        """Albums play artist"""
        artist_name = self.album_ctrl.GetItem(self.album_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.info("Albums item play %s", artist_name)
        self.mpd.play_artist_tag(artist_name)

    def on_menu_songs_append_song(self, _event) -> None:
        """Songs append song"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Songs item append song %s", song)
        self.mpd.append_song(song)
    def on_menu_songs_play_song(self, _event) -> None:
        """Songs play song"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Songs item play song %s", song)
        self.mpd.play_song(song)
    def on_menu_songs_append_album(self, _event) -> None:
        """Songs append album"""
        album = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Songs item append album %s", album)
        self.mpd.append_album_tag(album)
    def on_menu_songs_play_album(self, _event) -> None:
        """Songs play album"""
        album = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Songs item play album %s", album)
        self.mpd.play_album_tag(album)
    def on_menu_songs_append_artist(self, _event) -> None:
        """Songs append artist"""
        artist = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Songs item append artist %s", artist)
        self.mpd.append_artist_tag(artist)
    def on_menu_songs_play_artist(self, _event) -> None:
        """Songs play artist"""
        artist = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Songs item play artist %s", artist)
        self.mpd.play_artist_tag(artist)
    def on_menu_songs_append_newplaylist(self, _event) -> None:
        """Songs append to new playlist"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Songs item append to new playlist %s", song)
        new = MpdNewPlaylistFrame(
            song,
            self,
            title='New Playlist',
            size=(320,140))
        new.Show()
    def on_menu_songs_append_playlist(self, playlist, _event) -> None:
        """Songs append to playlist"""
        song = self.songs_ctrl.GetItem(self.songs_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Song item append to playlist %s", song)
        self.append_to_playlist(playlist, song)

    def on_menu_search_append_song(self, _event) -> None:
        """Search append song"""
        song = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Search item append song %s", song)
        self.mpd.append_song(song)
    def on_menu_search_play_song(self, _event) -> None:
        """Search play song"""
        song = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Search item play song %s", song)
        self.mpd.play_song(song)
    def on_menu_search_append_album(self, _event) -> None:
        """Search append album"""
        album = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Search item append album %s", album)
        self.mpd.append_album_tag(album)
    def on_menu_search_play_album(self, _event) -> None:
        """Search play album"""
        album = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=1).GetText()
        self.logger.debug("Search item play album %s", album)
        self.mpd.play_album_tag(album)
    def on_menu_search_append_artist(self, _event) -> None:
        """Search append artist"""
        artist = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Search item append artist %s", artist)
        self.mpd.append_artist_tag(artist)
    def on_menu_search_play_artist(self, _event) -> None:
        """Search play artist"""
        artist = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=2).GetText()
        self.logger.debug("Search item play artist %s", artist)
        self.mpd.play_artist_tag(artist)
    def on_menu_search_append_newplaylist(self, _event) -> None:
        """Search append to new playlist"""
        song = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Search item append to new playlist %s", song)
        new = MpdNewPlaylistFrame(
            song,
            self,
            title='New Playlist',
            size=(320,140))
        new.Show()
    def on_menu_search_append_playlist(self, playlist, _event) -> None:
        """Search append to playlist"""
        song = self.search_ctrl.GetItem(self.search_ctrl.GetFirstSelected(), col=6).GetText()
        self.logger.debug("Search item append to playlist %s", song)
        self.append_to_playlist(playlist, song)

    def append_to_playlist(self, playlist, file) -> None:
        self.mpd.playlist_add(playlist, file)
        
    def on_menu_playlist_load(self, _event: wx.CommandEvent) -> None:
        """Menu Playlist Load"""
        playlist = self.playlists_ctrl.GetItem(self.playlists_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.info("Playlist load %s", playlist)
        self.mpd.load(playlist)
    def on_menu_playlist_remove(self, _event: wx.CommandEvent) -> None:
        """Menu Playlist Remove"""
        playlist = self.playlists_ctrl.GetItem(self.playlists_ctrl.GetFirstSelected(), col=0).GetText()
        self.logger.info("Playlist remove %s", playlist)
        self.mpd.remove(playlist)

class MpdNewPlaylistFrame(wx.Frame):
    """New playlist window"""
    def __init__(self, file :str, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)

        self.file = file

        self.panel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        name_label = wx.StaticText(self.panel, label='Name')
        self.sizer.Add(name_label, 0, wx.EXPAND|wx.ALL, 1)

        self.name_text = wx.TextCtrl(self.panel, value='')
        self.sizer.Add(self.name_text, 0, wx.EXPAND|wx.ALL, 1)

        cancel_button = wx.Button(self.panel, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.sizer.Add(cancel_button, 0, wx.EXPAND|wx.ALL, 1)

        ok_button = wx.Button(self.panel, label="OK")
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)
        self.sizer.Add(ok_button, 0, wx.EXPAND|wx.ALL, 1)

    def on_ok(self, _event: wx.PyCommandEvent) -> None:
        """On ok"""
        self.logger.debug("on_ok()")
        self.Parent.append_to_playlist(self.name_text.Value, self.file)
        self.Close()

    def on_cancel(self, _event: wx.PyCommandEvent) -> None:
        """On cancel"""
        self.logger.debug("on_cancel()")
        self.Close()

class MpdSavePlaylistFrame(wx.Frame):
    """Save playlist window"""
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.info("Starting %s", type(self).__name__)
        
        self.panel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        name_label = wx.StaticText(self.panel, label='Name')
        self.sizer.Add(name_label, 0, wx.EXPAND|wx.ALL, 1)

        self.name_text = wx.TextCtrl(self.panel, value='')
        self.sizer.Add(self.name_text, 0, wx.EXPAND|wx.ALL, 1)

        cancel_button = wx.Button(self.panel, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.sizer.Add(cancel_button, 0, wx.EXPAND|wx.ALL, 1)

        save_button = wx.Button(self.panel, label="Save")
        self.Bind(wx.EVT_BUTTON, self.on_save, save_button)
        self.sizer.Add(save_button, 0, wx.EXPAND|wx.ALL, 1)

    def on_save(self, _event: wx.PyCommandEvent) -> None:
        """On save"""
        self.logger.debug("on_save()")
        self.Parent.mpd.save_playlist(self.name_text.Value)
        self.Close()

    def on_cancel(self, _event: wx.PyCommandEvent) -> None:
        """On cancel"""
        self.logger.debug("on_cancel()")
        self.Close()

class MpdPreferencesFrame(wx.Dialog):
    """Mpd preferences window"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-ancestors
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

        self.host_text = wx.TextCtrl(self.panel, value=self.preferences.get('host', ''))
        self.sizer.Add(self.host_text, 0, wx.EXPAND|wx.ALL, 1)

        port_label = wx.StaticText(self.panel, label='Port')
        self.sizer.Add(port_label, 0, wx.EXPAND|wx.ALL, 1)

        self.port_text = wx.TextCtrl(self.panel, value=self.preferences.get('port', ''))
        self.sizer.Add(self.port_text, 0, wx.EXPAND|wx.ALL, 1)

        username_label = wx.StaticText(self.panel, label='Username')
        self.sizer.Add(username_label, 0, wx.EXPAND|wx.ALL, 1)

        self.username_text = wx.TextCtrl(self.panel, value=self.preferences.get('username', ''))
        self.sizer.Add(self.username_text, 0, wx.EXPAND|wx.ALL, 1)

        password_label = wx.StaticText(self.panel, label='Password')
        self.sizer.Add(password_label, 0, wx.EXPAND|wx.ALL, 1)

        self.password_text = wx.TextCtrl(self.panel, value=self.preferences.get('password', ''))
        self.sizer.Add(self.password_text, 0, wx.EXPAND|wx.ALL, 1)

        self.notifications_check = wx.CheckBox(self.panel, label="Notifications")
        self.notifications_check.SetValue(
            self.preferences.get('notifications', DEFAULT_OPTION_NOTIFICATIONS))
        self.sizer.Add(self.notifications_check, 0, wx.EXPAND|wx.ALL, 1)

        self.mediakeys_check = wx.CheckBox(self.panel, label="Media keys")
        self.mediakeys_check.SetValue(
            self.preferences.get('mediakeys', DEFAULT_OPTION_MEDIAKEYS))
        self.sizer.Add(self.mediakeys_check, 0, wx.EXPAND|wx.ALL, 1)

        self.fetchallart_check = wx.CheckBox(self.panel, label="Fetch all art")
        self.fetchallart_check.SetValue(
            self.preferences.get('fetchallart', DEFAULT_OPTION_FETCHALLART))
        self.sizer.Add(self.fetchallart_check, 0, wx.EXPAND|wx.ALL, 1)

        cancel_button = wx.Button(self.panel, label="Cancel")
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.sizer.Add(cancel_button, 0, wx.EXPAND|wx.ALL, 1)

        save_button = wx.Button(self.panel, label="Save")
        self.Bind(wx.EVT_BUTTON, self.on_save, save_button)
        self.sizer.Add(save_button, 0, wx.EXPAND|wx.ALL, 1)

    def on_save(self, _event: wx.PyCommandEvent) -> None:
        """On save preferences"""
        self.logger.debug("on_save()")
        self.preferences.update({'host': self.host_text.Value})
        self.preferences.update({'port': self.port_text.Value})
        self.preferences.update({'username': self.username_text.Value})
        self.preferences.update({'password': self.password_text.Value})
        self.preferences.update({'notifications': self.notifications_check.Value})
        self.preferences.update({'mediakeys': self.mediakeys_check.Value})
        self.preferences.update({'fetchallart': self.fetchallart_check.Value})
        self.EndModal(wx.ID_SAVE)

    def on_cancel(self, _event: wx.PyCommandEvent) -> None:
        """On cancel preferences window"""
        self.logger.debug("on_cancel()")
        self.EndModal(wx.ID_CANCEL)

def main():
    """The main function for MPDCMD"""
    app = wx.App()
    frame = MpdCmdFrame(None, title='MPDCMD', size=(640,480))
    frame.SetIcon(get_icon('icon'))
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
