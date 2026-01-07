import os
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

# Loads our token as an environment variable
load_dotenv()
TOKEN: str = os.getenv("DISCORD_TOKEN")


class BotFella(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.music")



# Creates an Intents object that stores the permission configuration.
intents = discord.Intents.default()
# Bot can read and handle messages
intents.message_content = True

# Creates Bot object (represents our discord bot)
bot = BotFella(command_prefix="!", intents=intents)



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



bot.run(TOKEN)