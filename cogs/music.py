import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import asyncio
from collections import deque
from typing import Literal, Optional
import datetime
import random

class Music(commands.Cog):
    SONG_QUEUES = {}
    NOW_PLAYING = {}
    NUM_SEARCH_RESULTS = 10

    def __init__(self, bot):
        self.bot = bot

    class Song():
        def __init__(self, audio_url, title, user_id, username, duration, url, thumbnail):
            self.audio_url = audio_url
            self.title = title
            self.user_id = user_id
            self.username = username
            self.duration = duration
            self. url = url
            self. thumbnail = thumbnail
            

    @app_commands.command(name="play", description="Play a song or add it to the queue")
    @app_commands.describe(song_query="Search query")
    async def play(self, interaction: discord.Interaction, song_query: str):
        # Lets discord know that the action will take a long time
        await interaction.response.defer()

        voice_channel = None
        try:
            voice_channel = interaction.user.voice.channel
        except(AttributeError):
            await interaction.followup.send(embed=discord.Embed(title="You must be in a voice channel.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
            return
        
        # A voice client is an entity that can interact with voice channels in Discord
        # If a bot has a voice client, that means it is connected to a voice channel
        voice_client = interaction.guild.voice_client

        # Joins a voice channel if not in one, and moves to the correct voice channel if in the wrong one
        if voice_client is None:
            voice_client = await voice_channel.connect(self_deaf=True)
        elif voice_channel != voice_client.channel:
            await voice_client.move_to(voice_channel)

        message = await interaction.followup.send(embed=discord.Embed(title=f"Searching for... {song_query}", color=discord.Color.light_embed(), timestamp=datetime.datetime.now()))

        url = None

        if is_link(song_query):
            url = song_query
        else:
            url = await self.search_for_song_url(interaction, song_query, message.id)
            if url == 0:
                return
            if url is None:
                return await interaction.followup.edit_message(message_id=message.id, embed=discord.Embed(title="No results found.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
        
        await interaction.followup.edit_message(message_id=message.id, embed=discord.Embed(title="Queueing song...", color=discord.Color.light_embed(), timestamp=datetime.datetime.now()))
        
        ydl_play_options = {
            "format": "bestaudio[abr<=96]/bestaudio",
            "noplaylist": True,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "skip_download": True
        }
        
        selected_track = await search_ytdlp_async(url, ydl_play_options)
        
        
        audio_url = selected_track["url"]
        title = selected_track.get("title", "Unititled")
        user_id = interaction.user.id
        username = interaction.user.nick if interaction.user.nick else interaction.user.display_name 
        duration = selected_track["duration"]
        thumbnail = selected_track["thumbnail"]

        # Gets the current server id
        guild_id = str(interaction.guild_id)
        # Creates a new queue for the server is one does not already exist
        if Music.SONG_QUEUES.get(guild_id) is None:
            Music.SONG_QUEUES[guild_id] = deque()

        # Adds song to queue
        Music.SONG_QUEUES[guild_id].append(Music.Song(audio_url, title, user_id, username, duration, url, thumbnail))

        queued_embed = discord.Embed(title="Track enqueued!", description=f"[{title}]({url})", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
        queued_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        queued_embed.set_thumbnail(url=thumbnail)
        await interaction.followup.edit_message(message_id=message.id, embed=queued_embed)

        # Checks if a song is currently playing
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await self.play_next_song(voice_client, guild_id, interaction.channel)


    @app_commands.command(name="skip", description="Skips the current playing song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        guild_id = str(interaction.guild_id)
        song = Music.NOW_PLAYING[guild_id]

        # Checks to see if something playing and stops it if so, which triggers our function to play the next song
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            embed = embed=discord.Embed(title="Skipped the current song!", description=f"[{song.title}]({song.url})", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
            embed.set_thumbnail(url=song.thumbnail)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=discord.Embed(title="Not playing anything to skip.", color=discord.Color.red(), timestamp=datetime.datetime.now()))



    @app_commands.command(name="pause", description="Pause the currently playing song.")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        # Checks if the bot is in a voice channel
        if voice_client is None:
            return await interaction.response.send_message(embed=discord.Embed(title="I am not in a voice channel.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
        
        # Checks if something is actually playing
        if not voice_client.is_playing():
            return await interaction.response.send_message(embed=discord.Embed(title="Nothing is currently playing.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
        
        # Pauses the track
        voice_client.pause()
        embed = discord.Embed(title="Playback paused!", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="resume", description="Resume the currently paused song.")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        # Checks if the bot is in a voice channel
        if voice_client is None:
            return await interaction.response.send_message(embed=discord.Embed(title="I am not in a voice channel.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
        
        # Checks if something is actually playing
        if not voice_client.is_paused():
            return await interaction.response.send_message(embed=discord.Embed(title="I am not paused right now.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
        
        # Resumes the track
        voice_client.resume()
        embed = discord.Embed(title="Playback resumed!", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="stop", description="Stop playback and clear the queue.")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        voice_client = interaction.guild.voice_client
        
        # Checks if the bot is in a voice channel
        if not voice_client or not voice_client.is_connected():
            return await interaction.followup.send(embed=discord.Embed(title="I am not connected to any voice channel.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
        
        # Clear the server's queue
        guild_id_str = str(interaction.guild_id)
        if guild_id_str in Music.SONG_QUEUES:
            Music.SONG_QUEUES[guild_id_str].clear()
        
        # If something is playing or paused, stop it
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        embed = discord.Embed(title="Stopped playback and disconnected!", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

        # Disconnects from channel
        await voice_client.disconnect()




    @app_commands.command(name="queue", description="Displays the current queue")
    async def queue(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        voice_client = interaction.guild.voice_client

        if Music.SONG_QUEUES.get(guild_id, deque()) == deque() and not voice_client or not voice_client.is_connected():
            await interaction.response.send_message(embed=discord.Embed(title="The queue is currently empty.", color=discord.Color.red(), timestamp=datetime.datetime.now()))
            return

        embed = discord.Embed(title="Music Queue", color=discord.Color.light_embed())
        total_duration = 0

        if voice_client.is_playing() or voice_client.is_paused():
            embed.description = f"Now Playing: {Music.NOW_PLAYING[guild_id].title}"

        count = 1
        for song in Music.SONG_QUEUES[guild_id]:
            embed.add_field(name=f"{count} - {song.title}", value=f"requested by {song.username}", inline=False)
            total_duration += song.duration

            count += 1

        embed.set_footer(text=f"Estimated time remaining: {total_duration // 60}m {total_duration % 60}s")
        
        await interaction.response.send_message(embed=embed)



    async def search_for_song_url(self, interaction: discord.Interaction, song_query, message_id):
        # Logic for searching for yt video
        ydl_search_options = {
            "format": "bestaudio[abr<=96]/bestaudio",
            "noplaylist": True,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "skip_download": True,
            "extract_flat": True
        }

        query = f"ytsearch{Music.NUM_SEARCH_RESULTS}: " + song_query
        results = await search_ytdlp_async(query, ydl_search_options)
        tracks = results.get("entries", [])

        if tracks is None or tracks == []:
            return None

        
        select_embed = discord.Embed(title="Type in chat the number you want to play", description="Not entering a number will make it play the first match", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
        select_embed.add_field(name="0 - Cancel", value="Cancels the request.", inline=False)
        count = 1
        for track in tracks:
            select_embed.add_field(name=f"{count} - {track.get("title", "Untitled")}", value=track.get("channel"), inline=False)
            count += 1
        message = await interaction.followup.edit_message(message_id=message_id, embed=select_embed)
        
        def check(m):
            return interaction.user == m.author and m.content.isdigit() and int(m.content) >= 0 and int(m.content) <= len(tracks)
        msg = None
        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            msg = msg.content
        except(TimeoutError):
            msg = 1
        track_index = int(msg)

        if track_index == 0:
            return_embed = discord.Embed(title="Play request cancelled.", color=discord.Color.yellow(), timestamp=datetime.datetime.now())
            await interaction.followup.edit_message(message_id=message.id, embed=return_embed)
            return 0
        
        selected_track = tracks[track_index - 1]
        return selected_track["url"]



    async def play_next_song(self, voice_client, guild_id, channel):
        if Music.SONG_QUEUES[guild_id]:
            # Gets next song for the current server's queue
            Music.NOW_PLAYING[guild_id] = Music.SONG_QUEUES[guild_id].popleft()
            audio_url = Music.NOW_PLAYING[guild_id].audio_url
            title = Music.NOW_PLAYING[guild_id].title
            original_url = Music.NOW_PLAYING[guild_id].url
            thumbnail = Music.NOW_PLAYING[guild_id].thumbnail

            # Logic for playing the song
            ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k"
        }

            source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="/usr/bin/ffmpeg")

            def after_play(error):
                if (error):
                    print(f"Error playing {title}: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next_song(voice_client, guild_id, channel), self.bot.loop)

            voice_client.play(source, after=after_play)

            embed = embed=discord.Embed(title="Now playing!", description=f"[{title}]({original_url})", color=discord.Color.light_embed(), timestamp=datetime.datetime.now())
            embed.set_thumbnail(url=thumbnail)
            asyncio.create_task(channel.send(embed=embed))

        else:
            # Leaves when queue is empty
            await voice_client.disconnect()
            Music.SONG_QUEUES[guild_id] = deque()
    



async def setup(bot):
    await bot.add_cog(Music(bot))


 
# Helper functions

async def search_ytdlp_async(query, ydl_opts):
    '''Handles concurrent execution'''
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    '''Performs search'''
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)
        

def is_link(query: str):
    '''Checks if a query is a link'''
    return query.startswith("https://www.youtube.com/watch") or query.startswith("https://youtu.be/")