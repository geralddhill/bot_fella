import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import asyncio
from collections import deque
from typing import Literal, Optional

from keep_alive import keep_alive

# Loads our token as an environment variable
load_dotenv()
TOKEN: str = os.getenv("DISCORD_TOKEN")

SONG_QUEUES = {}

keep_alive()



# Handles concurrent execution
async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

# Performs search
def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)



# Creates an Intents object that stores the permission configuration.
intents = discord.Intents.default()
# Bot can read and handle messages
intents.message_content = True

# Creates Bot object (represents our discord bot)
bot = commands.Bot(command_prefix="!", intents=intents)



# An event is just something that happens in the discord server (joining the server, joining a vc, sending a msg, etc)
# The bot.event decorator is so Discord knows we are working with an event handler
@bot.event
# The on_ready event runs when the bot comes online, so we call its event handler
async def on_ready():
    print(f"{bot.user} is online!")



@bot.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")



# The bot keeps track of its commands using a tree
# This decorator tells the bot to create a new slash command and add it to the tree
@bot.tree.command(name="greet", description='Sends a greeting to the user')
# This just defines the function that will run when the command is called
# An Interaction is an object that contains all the information about the specific command usage
# (the user that ran the command, the channel in which it was used, etc)
async def greet(interaction: discord.Interaction):
    username = interaction.user.mention
    await interaction.response.send_message(f"Hello there, {username}")


@bot.tree.command(name="play", description="Play a song or add it to the queue")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    # Lets discord know that the action will take a long time
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return
    
    # A voice client is an entity that can interact with voice channels in Discord
    # If a bot has a voice client, that means it is connected to a voice channel
    voice_client = interaction.guild.voice_client

    # Joins a voice channel if not in one, and moves to the correct voice channel if in the wrong one
    if voice_client is None:
        voice_client = await voice_channel.connect(self_deaf=True)
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    # Logic for searching for yt video
    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
        "--cookies": "cookies.txt"
    }

    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    if tracks is None:
        await interaction.followup.send("No results found.")
        return
    
    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Unititled")

    # Gets the current server id
    guild_id = str(interaction.guild_id)
    # Creates a new queue for the server is one does not already exist
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    # Adds song to queue
    SONG_QUEUES[guild_id].append((audio_url, title))

    # Checks if a song is currently playing
    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        await play_next_song(voice_client, guild_id, interaction.channel)
    


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Checks to see if something playing and stops it if so, which triggers our function to play the next song
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("Not playing anything to skip.")



@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Checks if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I am not in a voice channel.")
    
    # Checks if something is actually playing
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    
    # Pauses the track
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")



@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Checks if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I am not in a voice channel.")
    
    # Checks if something is actually playing
    if not voice_client.is_paused():
        return await interaction.response.send_message("I am not paused right now.")
    
    # Pauses the track
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")



@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client
    
    # Checks if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        return await interaction.followup.send("I'm not connected to any voice channel.")
    
    # Clear the server's queue
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()
    
    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await interaction.followup.send("Stopped playback and disconnected!")

    # Disconnects from channel
    await voice_client.disconnect()



async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        # Gets next song for the current server's queue
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        # Logic for playing the song
        ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k"
    }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

        def after_play(error):
            if (error):
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))

    else:
        # Leaves when queue is empty
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()


bot.run(TOKEN)