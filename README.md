# Bot Fella

Bot Fella is a Discord bot that searches for and plays YouTube videos in a discord voice call!

## Motivation

Recently, most YouTube discord bots have been taken down, so I used my programming experience to make a bot for personal use by me and my friends, who like having background music in our Discord calls. This also allows me to customize the bot to fit our needs and leave out all of the junk that we don't need.

## Quick Start

This bot can now be installed using Docker! You can view the image on Docker Hub [here](https://hub.docker.com/r/geralddhill/bot_fella).

1. Setup your Discord bot in the [Discord Developer Portal](https://discord.com/developers/applications)

2. In the **Bot** tab in your application, click **Reset Token** and copy the token. **DO NOT SHARE THIS TOKEN WITH ANYONE!**

3. Paste the following into your docker-compose.yaml file:

    ```
    services:
      bot-fella:
        image: geralddhill/bot_fella
        environment:
          DISCORD_TOKEN: [paste token here]
    ```

    Don't forget to paste the token you just copied!

4. Run the docker container:
    ```
    docker compose up
    ```

## Usage

**/play \[song-query\]**: Searches for a video on youtube and displays top 10 results back to the user. The user can pick which one to queue up and play.

**/queue**: Displays the current queue to the user.

**/pause** & **/resume**: Pauses and resumes playback.

**/stop**: Immediately ceases playback and disconnects from voice channel.

**/greet**: Sends a greeting to the user.

**!sync**: Admin-only command that syncs any changes to the command tree (only necessary if adding your own commands).

### Disclaimer

DO NOT use this library to downloaded copywrighted material. I am not responsible for any copyright violations using this bot.

## Contribution

If you like to start contributing, here are the steps to get your local dev instance up and running:

1. Fork and clone the repository

2. Install the required libraries by running the following in your command line:

    ```
    pip install -r requirements.txt
    ```

    Note: It is highly reccomened to run this in a [virtual environment](https://docs.python.org/3/library/venv.html) to prevent version conflicts with your other projects

3. Create and checkout into a new branch:

    ```
    git branch your_branch_name
    git checkout your_branch_name
    ```

4. Setup your Discord bot in the [Discord Developer Portal](https://discord.com/developers/applications)

5. In the **Bot** tab in your application, click **Reset Token** and copy the token. **DO NOT SHARE THIS TOKEN WITH ANYONE!** Then create a file called **.env** and paste the token like so:
    ```
    DISCORD_TOKEN=your_token_here
    ```

6. Run bot_fella.py:
    ```
    python bot_fella.py
    ```

 

If there are any issues with Bot Fella, make sure to create an issue so we can track it!

If you're planning to contribute, make sure your contribution references and issue, and if there isn't one that matches your contribution, create one!

When you have finished your contribution, create a pull request to merge it into the main branch!
