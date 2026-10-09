import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from collections import deque
import datetime

from src.models.music_handler import MusicHandler
from src.views.music_view import error_embed, default_embed, detailed_embed, select_embed, queue_embed



class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_handler = MusicHandler()

    @app_commands.command(name="play", description="Play a song or add it to the queue")
    @app_commands.describe(song_query="Search query")
    async def play(self, interaction: discord.Interaction, song_query: str):
        # Lets discord know that the action will take a long time
        await interaction.response.defer()

        # Makes sure use who sent the command is in a voice channel
        voice_channel = None
        try:
            voice_channel = interaction.user.voice.channel
        except AttributeError:
            await interaction.followup.send(embed=error_embed("You must be in a voice channel."))
            return
        
        # A voice client is an entity that can interact with voice channels in Discord
        # If a bot has a voice client, that means it is connected to a voice channel
        voice_client = interaction.guild.voice_client

        # Joins a voice channel if not in one, and moves to the correct voice channel if in the wrong one
        if voice_client is None:
            voice_client = await voice_channel.connect(self_deaf=True)
        elif voice_channel != voice_client.channel:
            await voice_client.move_to(voice_channel)

        message = await interaction.followup.send(embed=default_embed(f"Searching..."))

        url = None

        if self.music_handler.is_valid_url(song_query):
            url = song_query
        else:
            url = await self.search_for_song_url(interaction, song_query, message.id)
            if url == "":
                return_embed = discord.Embed(title="Play request cancelled.", color=discord.Color.yellow(),
                                             timestamp=datetime.datetime.now())
                await interaction.followup.edit_message(message_id=message.id, embed=return_embed)
                return
        if url is None:
            await interaction.followup.edit_message(message_id=message.id, embed=error_embed("No results found."))
            return
        
        await interaction.followup.edit_message(message_id=message.id, embed=default_embed("Queueing song..."))
        
        selected_tracks, title, thumbnail_url = await self.music_handler.get_songs_from_url(url, interaction.user)

        # Gets the current server id
        guild_id = interaction.guild_id

        # Adds song to queue
        for track in selected_tracks:
            self.music_handler.queue_song(guild_id, track)

        await interaction.followup.edit_message(message_id=message.id, embed=detailed_embed(
            message=f"{"Playlist" if len(selected_tracks) > 1 else "Track"} Queued!",
            title=title,
            url=url,
            name=interaction.user.name,
            avatar_url=interaction.user.display_avatar.url,
            thumbnail_url=thumbnail_url,
        ))

        # Checks if a song is currently playing
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await self.play_next_song(voice_client, guild_id, interaction.channel)


    @app_commands.command(name="skip", description="Skips the current playing song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild_id
        song = self.music_handler.get_now_playing(guild_id)

        # Checks to see if something playing and stops it if so, which triggers our function to play the next song
        if (not voice_client) or (song is None) or not (voice_client.is_playing() or voice_client.is_paused()):
            await interaction.response.send_message(embed=error_embed("Not playing anything to skip."))
            return

        voice_client.stop()
        await interaction.response.send_message(embed=detailed_embed(
            message="Skipped the current song!",
            title=song.title,
            url=song.url,
            name=interaction.user.name,
            avatar_url=interaction.user.display_avatar.url,
            thumbnail_url=song.thumbnail
        ))




    @app_commands.command(name="pause", description="Pause the currently playing song.")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        # Checks if the bot is in a voice channel
        if voice_client is None:
            await interaction.response.send_message(embed=error_embed("I am not connected to any voice channel."))
            return
        
        # Checks if something is actually playing
        if not voice_client.is_playing():
            await interaction.response.send_message(embed=error_embed("Nothing is currently playing."))
            return
        
        # Pauses the track
        voice_client.pause()
        await interaction.response.send_message(embed=detailed_embed(
            message="Playback paused!",
            name=interaction.user.name,
            url=interaction.user.display_avatar.url,
        ))



    @app_commands.command(name="resume", description="Resume the currently paused song.")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        # Checks if the bot is in a voice channel
        if voice_client is None:
            await interaction.response.send_message(embed=error_embed("I am not connected to any voice channel."))
            return
        
        # Checks if something is actually playing
        if not voice_client.is_paused():
            await interaction.response.send_message(embed=error_embed("Nothing is currently playing."))
            return
        
        # Resumes the track
        voice_client.resume()
        await interaction.response.send_message(embed=detailed_embed(
            message="Playback resumed!",
            name=interaction.user.name,
            url=interaction.user.display_avatar.url,
        ))



    @app_commands.command(name="stop", description="Stop playback and clear the queue.")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        voice_client = interaction.guild.voice_client
        
        # Checks if the bot is in a voice channel
        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send(embed=error_embed("I am not connected to any voice channel."))
            return
        
        # Clear the server's queue
        guild_id = interaction.guild_id
        self.music_handler.clear_queue(guild_id)
        
        # If something is playing or paused, stop it
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        await interaction.followup.send(embed=detailed_embed(
            message="Stopped playback and disconnected!",
            name=interaction.user.name,
            url=interaction.user.display_avatar.url,
        ))

        # Disconnects from channel
        await voice_client.disconnect()




    @app_commands.command(name="queue", description="Displays the current queue")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        voice_client = interaction.guild.voice_client

        if self.music_handler.queue_is_empty(guild_id) and not voice_client or not voice_client.is_connected():
            await interaction.response.send_message(embed=error_embed("The queue is currently empty."))
            return

        queue = self.music_handler.get_queue(guild_id)
        now_playing = self.music_handler.get_now_playing(guild_id)

        embed = queue_embed(queue=queue, now_playing=now_playing) if (voice_client.is_playing() or voice_client.is_paused()) else queue_embed(queue=queue)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dequeue", description="Remove a song from the queue")
    @app_commands.describe(song_num="Number of song to remove")
    async def dequeue(self, interaction: discord.Interaction, song_num: str):
        # Validate song_num
        if not song_num.isnumeric() or int(song_num) < 1:
            await interaction.response.send_message(embed=error_embed("Please enter a positive integer."))
            return

        guild_id = interaction.guild_id
        queue = self.music_handler.get_queue(guild_id)
        index = int(song_num)

        if index > len(queue):
            await interaction.response.send_message(embed=error_embed("Invalid song number."))
            return

        voice_client = interaction.guild.voice_client

        if queue == deque() and not voice_client or not voice_client.is_connected():
            await interaction.response.send_message(embed=error_embed("The queue is currently empty."))
            return

        # Converts song number that end user sees into list index in python
        index -= 1
        song = queue[index]

        if song.user_id != interaction.user.id:
            await interaction.response.send_message(embed=error_embed("You can only dequeue songs you have queued."))
            return


        self.music_handler.dequeue_song(guild_id, index)

        await interaction.response.send_message(embed=detailed_embed(
            message="Track dequeued!",
            title=song.title,
            url=song.url,
            name=interaction.user.name,
            avatar_url=interaction.user.display_avatar.url,
            thumbnail_url=song.thumbnail,
        ))
        

        



    async def search_for_song_url(self, interaction: discord.Interaction, song_query, message_id):
        tracks = await self.music_handler.search(song_query)

        if not tracks:
            return None

        message = await interaction.followup.edit_message(message_id=message_id, embed=select_embed(tracks))
        
        def check(m):
            return interaction.user == m.author and m.content.isdigit() and 0 <= int(m.content) <= len(tracks)

        msg = None
        try:
            msg = await self.bot.wait_for('message', timeout=20.0, check=check)
            msg = msg.content
        except TimeoutError:
            msg = 1
        user_input = int(msg)

        if user_input == 0:
            return ""
        
        selected_track = tracks[user_input - 1]
        return selected_track.url



    async def play_next_song(self, voice_client, guild_id, channel):
        if self.music_handler.get_queue(guild_id) == deque():
            # Leaves when queue is empty
            await voice_client.disconnect()
            return

        # Gets next song for the current server's queue
        self.music_handler.advance_queue(guild_id)
        now_playing = self.music_handler.get_now_playing(guild_id)
        audio_url = now_playing.audio_url
        title = now_playing.title
        original_url = now_playing.url
        thumbnail = now_playing.thumbnail

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

        asyncio.create_task(channel.send(embed=detailed_embed(
            message="Now playing!",
            title=title,
            url=original_url,
            thumbnail_url=thumbnail,
        )))




async def setup(bot):
    await bot.add_cog(Music(bot))