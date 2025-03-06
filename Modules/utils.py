import os
import shutil
import asyncio

TEMP_DIR = "Mohini_temp"

def cleanup_temp_files():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

async def cleanup_task():
    while True:
        await asyncio.sleep(600)  # 10 minutes
        cleanup_temp_files()
