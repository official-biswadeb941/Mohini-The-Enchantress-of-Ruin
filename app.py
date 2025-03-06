import os
import sys
import socket
import getpass
from datetime import datetime
from discord.ext import commands
import asyncio
from Modules.config import load_config
from Modules.bot import setup_bot
from Modules.utils import cleanup_task
from Modules.updater import update_repo, is_git_repo  # Import updater module

# Load config
config = load_config()
TOKEN = config["TOKEN"]

# Setup bot
bot = setup_bot()

# Run updater before starting the bot
if is_git_repo():
    update_repo()
else:
    print("This is not a Git repository. Please make sure you're in a cloned repository.")

# Periodic cleanup
async def background_tasks():
    await cleanup_task()

@bot.event
async def on_ready():
    hostname = socket.gethostname()  # Get system hostname
    username = getpass.getuser()  # Get logged-in username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time
    online_message = f"\U0001F525 **Mohini - ({hostname}) ({username}) is online at ({current_time}).** \U0001F525"
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(online_message)
                break
    asyncio.create_task(background_tasks())

# Run the bot
bot.run(TOKEN)
