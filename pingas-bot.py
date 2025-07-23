import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Loads our token as an environment variable
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

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
    await bot.tree.sync()
    print(f"{bot.user} is online!")

@bot.event
# on_message gets called whenever someone sends a message on ther server
async def on_message(msg):
    if msg.author.id != bot.user.id:
        await msg.channel.send(f"Interesting message, {msg.author.mention}")

# The bot keeps track of its commands using a tree
# This decorator tells the bot to create a new slash command and add it to the tree

@bot.tree.command(name="greet", description='Sends a greeting to the user')
# This just defines the function that will run when the command is called
# An Interaction is an object that contains all the information about the specific command usage
# (the user that ran the command, the channel in which it was used, etc)
async def greet(interaction: discord.Interaction):
    username = interaction.user.mention
    await interaction.response.send_message(f"Hello there, {username}")

bot.run(TOKEN)