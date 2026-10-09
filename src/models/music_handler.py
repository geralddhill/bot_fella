from src.models.url_handler import URLHandler
from src.models.song import Song, SongSearchResult
from collections import deque
import asyncio
import yt_dlp
import discord

from src.models.youtube_url_handler import YoutubeURLHandler


class MusicHandler:

    NUM_SEARCH_RESULTS = 10

    def __init__(self):
        self._song_queues: dict[int, deque[Song]] = {}
        self._now_playing: dict[int, Song] = {}
        self._link_handlers: list[URLHandler] = [YoutubeURLHandler()]

    def add_link_handler(self, link_handler: URLHandler):
        self._link_handlers.append(link_handler)

    # Queue Functionality
    def queue_song(self, guild_id: int, song: Song) -> None:
        # Creates a new queue for the server is one does not already exist
        if self._song_queues.get(guild_id) is None:
            self._song_queues[guild_id] = deque()

        self._song_queues[guild_id].append(song)

    def get_queue(self, guild_id: int) -> deque[Song]:
        return self._song_queues.get(guild_id, deque())

    def dequeue_song(self, guild_id: int, index: int) -> None:
        del self._song_queues[guild_id][index]

    def clear_queue(self, guild_id: int) -> None:
        if guild_id in self._song_queues.keys():
            self._song_queues[guild_id].clear()

    def queue_is_empty(self, guild_id: int) -> bool:
        return self._song_queues.get(guild_id, deque()) == deque()

    def get_now_playing(self, guild_id: int) -> Song | None:
        return self._now_playing.get(guild_id, None)

    def advance_queue(self, guild_id:int) -> None:
        if guild_id not in self._song_queues.keys():
            raise ValueError("Guild does not have a queue.")

        self._now_playing[guild_id] = self._song_queues[guild_id].popleft()


    # Download Functionality

    @staticmethod
    async def search(query: str) -> list[SongSearchResult]:
        # Logic for searching for yt video
        ydl_search_options = {
            "format": "bestaudio[abr<=96]/bestaudio",
            "noplaylist": True,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "skip_download": True,
            "extract_flat": True
        }

        ydl_query = f"ytsearch{MusicHandler.NUM_SEARCH_RESULTS}: " + query
        results = await MusicHandler.search_ytdlp_async(ydl_query, ydl_search_options)
        tracks = results.get("entries", [])

        if tracks is None:
            return []

        return list(map(lambda song: SongSearchResult(song.get("title", "Untitled"), song.get("channel"), song["url"]), tracks))

    async def get_songs_from_url(self, url: str, user: discord.User) -> tuple[list[Song], str, str]:
        url_handler = next((h for h in self._link_handlers if h.can_handle(url)), None)
        if url_handler is None:
            raise ValueError("Invalid URL.")

        yt_url = url_handler.to_youtube_url(url)

        ydl_play_options = {
            "format": "bestaudio[abr<=96]/bestaudio",
            "noplaylist": True,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "skip_download": True
        }

        ytdlp_response = await MusicHandler.search_ytdlp_async(yt_url, ydl_play_options)
        user_id = user.id
        username = user.nick if user.nick else user.display_name

        if ytdlp_response.get("entries") is None:
            audio_url = ytdlp_response["url"]
            title = ytdlp_response.get("title", "Untitled")
            duration = ytdlp_response["duration"]
            thumbnail = ytdlp_response["thumbnail"]
            return [Song(audio_url, title, user_id, username, duration, yt_url, thumbnail)], title, thumbnail

        result = []

        for song in ytdlp_response["entries"]:
            audio_url = song["url"]
            title = song.get("title", "Untitled")

            duration = song["duration"]
            thumbnail = song["thumbnail"]
            result.append(Song(audio_url, title, user_id, username, duration, yt_url, thumbnail))

        return result, ytdlp_response.get("title", "Untitled"), ytdlp_response["thumbnails"][0]["url"]

    def is_valid_url(self, query: str) -> bool:
        """Checks if a query is a link"""
        return any((h for h in self._link_handlers if h.can_handle(query)))

    @staticmethod
    async def search_ytdlp_async(query, ydl_opts):
        """Handles concurrent execution"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: MusicHandler._extract(query, ydl_opts))

    @staticmethod
    def _extract(query, ydl_opts):
        """Performs search"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)