# Bot Fella

Bot Fella is a Discord bot that searches for and plays YouTube videos in a discord voice call!

## Motivation

Recently, most YouTube discord bots have been taken down, so I used my programming experience to make a bot for personal use by me and my friends, who like having background music in our Discord calls. This also allows me to customize the bot to fit our needs and leave out all of the junk that we don't need.

## Quick Start

1. Download the [latest release](https://github.com/geralddhill/bot_fella/releases/tag/v0.1.0).

2. Install the required libraries by running the following in your command line:
```
pip install -r requirements.txt
```

Note: It is highly reccomened to run this in a [virtual environment](https://docs.python.org/3/library/venv.html) to prevent version conflicts with your other projects

3. Setup your Discord bot in the [Discord Developer Portal](https://discord.com/developers/applications)

4. In the **Bot** tab in your application, click **Reset Token** and copy the token. **DO NOT SHARE THIS TOKEN WITH ANYONE!** Then create a file called **.env** and paste the token like so:
```
DISCORD_TOKEN=your_token_here
```

5. Run bot_fella.py:
```
python bot_fella.py
```

## Usage

**/play \[song-query\]**: Searches for a video on youtube and displays top 10 results back to the user. The user can pick which one to queue up and play.

**/queue**: Displays the current queue to the user.

**/pause** & **/resume**: Pauses and resumes playback.

**/stop**: Immediately ceases playback and disconnects from voice channel.

**/greet**: Sends a greeting to the user.

**!sync**: Admin-only command that syncs any changes to the command tree (only necessary if adding your own commands).

## Disclaimer

DO NOT use this library to downloaded copywrighted material. I am not responsible for any copywright violations using this bot.
