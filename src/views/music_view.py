import discord
import datetime
from src.models.song import Song, SongSearchResult
from collections import deque

def default_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title=message,
        color=discord.Color.light_embed(),
        timestamp=datetime.datetime.now()
    )

def error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title=message,
        color=discord.Color.red(),
        timestamp=datetime.datetime.now()
    )

def detailed_embed(message: str, title: str, url: str, name: str, avatar_url: str, thumbnail_url: str) -> discord.Embed:
    embed = discord.Embed(
        title=message,
        description=f"[{title}]({url})",
        color=discord.Color.light_embed(),
        timestamp=datetime.datetime.now()
    )
    embed.set_author(name=name, icon_url=avatar_url)
    embed.set_thumbnail(url=thumbnail_url)

    return embed

def select_embed(tracks: list[SongSearchResult]) -> discord.Embed:
    embed = discord.Embed(title="Type in chat the number you want to play",
                                 description="Not entering a number will make it play the first match",
                                 color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
    embed.add_field(name="0 - Cancel", value="Cancels the request.", inline=False)
    count = 1
    for track in tracks:
        embed.add_field(name=f"{count} - {track.title}", value=track.channel,
                               inline=False)
        count += 1

    return embed

def queue_embed(queue: deque[Song], now_playing: str = None) -> discord.Embed:
    embed = discord.Embed(title="Music Queue", color=discord.Color.light_embed())
    total_duration = 0

    if now_playing is not None:
        embed.description = f"Now Playing: {now_playing.title}"

    count = 1
    for song in queue:
        embed.add_field(name=f"{count} - {song.title}", value=f"requested by {song.username}", inline=False)
        total_duration += song.duration

        count += 1

    embed.set_footer(text=f"Estimated time remaining: {total_duration // 60}m {total_duration % 60}s")

    return embed