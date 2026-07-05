import asyncio
import discord
from discord.ext import commands
from fastapi import FastAPI
import uvicorn
import threading
import os

from config import TOKEN
from bot_base import bot
import human_bingo

# FastAPI App for Health Checks / Vercel
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot is alive"}

@app.get("/health")
async def health():
    return {"status": "ok", "latency": round(bot.latency * 1000, 2) if bot.is_ready() else "connecting"}

async def load_extensions():
    extensions = [
        "cogs.general",
        "cogs.tasks",
        "cogs.wings",
        "cogs.meetings",
        "cogs.analytics",
        "cogs.admin",
        "cogs.events"
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

@bot.event
async def on_ready():
    # Human Bingo setup
    if not getattr(bot, 'bingo_loaded', False):
        try:
            await human_bingo.setup(bot)
            bot.bingo_loaded = True
            print("✅ Human Bingo module loaded.")
        except Exception as e:
            print(f"❌ Human Bingo load failed: {e}")
    
    # Reload role view dynamically for persistence
    # This logic is also in EventsCog, but keeping it here as a backup for now
    print(f"🚀 {bot.user} is online and operational!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    print(f"❌ Command Error: {error}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Start API in a separate thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Run bot in main thread
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
else:
    # Vercel / Production entry point
    @app.on_event("startup")
    async def startup_event():
        asyncio.create_task(main())
