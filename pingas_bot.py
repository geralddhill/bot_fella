import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import asyncio

# Loads our token as an environment variable
load_dotenv()
TOKEN: str = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1397650988084756480



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
    test_guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=test_guild)
    
    print(f"{bot.user} is online!")



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

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False
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

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k"
    }

    source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

    voice_client.play(source)



bot.run(TOKEN)