import discord
from discord.ext import commands
from .commands import register_commands

def setup_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"Bot is ready! Logged in as {bot.user}")
    
    register_commands(bot)
    
    return bot
