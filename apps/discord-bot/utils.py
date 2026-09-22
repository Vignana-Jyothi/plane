import requests
import json
import asyncio
import discord
from datetime import datetime, timezone
from config import APPSCRIPT_URL, LOG_CHANNEL_ID, REMINDER_CHANNEL_ID, MASTER_KEYWORDS
from bot_base import bot

def _sync_apps_post(sheet, payload, guild=None):
    """Synchronous implementation of posting to Apps Script"""
    try:
        url = f"{APPSCRIPT_URL}?sheet={sheet}"
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=60)
        r.raise_for_status()
        
        if "errorMessage" in r.text or "TypeError" in r.text:
            raise Exception(f"Apps Script Error: {r.text[:200]}")
        
        print(f"✅ POST {sheet}: Success ({r.status_code})")
        return r
    except Exception as e:
        err_msg = f"❌ Error posting to Apps Script ({sheet}): {e}"
        print(err_msg)
        print(f"Payload was: {json.dumps(payload, indent=2)}")
        if guild:
            asyncio.run_coroutine_threadsafe(send_log(guild, err_msg), bot.loop)
        return None

async def apps_post(sheet, payload, guild=None):
    """Post data to Google Apps Script asynchronously"""
    return await bot.loop.run_in_executor(None, _sync_apps_post, sheet, payload, guild)

def _sync_apps_get(sheet, wing=None, guild=None):
    """Synchronous implementation of getting data from Apps Script"""
    try:
        url = f"{APPSCRIPT_URL}?sheet={sheet}"
        if wing:
            url += f"&wing={wing}"
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        
        if isinstance(r.text, str) and ("errorMessage" in r.text or "TypeError" in r.text):
            raise Exception(f"Apps Script Error: {r.text[:200]}")

        return r.json()
    except Exception as e:
        err_msg = f"❌ Error fetching from Apps Script ({sheet}{f' - {wing}' if wing else ''}): {e}"
        print(err_msg)
        if guild:
            asyncio.run_coroutine_threadsafe(send_log(guild, err_msg), bot.loop)
        return []

async def apps_get(sheet, wing=None, guild=None):
    """Get data from Google Apps Script asynchronously"""
    return await bot.loop.run_in_executor(None, _sync_apps_get, sheet, wing, guild)

async def send_reminder(guild, content=None, embed=None, channel_id=None):
    """Send reminder to a specific channel or fallback to configured reminder channel"""
    target_id = channel_id or REMINDER_CHANNEL_ID
    
    if not target_id:
        target_id = LOG_CHANNEL_ID
    
    if not target_id:
        return
        
    try:
        channel = guild.get_channel(int(target_id))
        if channel:
            if embed:
                await channel.send(content=content, embed=embed)
            else:
                await channel.send(content)
    except Exception as e:
        print(f"Error sending to reminder channel {target_id}: {e}")

async def send_log(guild, content=None, embed=None):
    """Send log message to designated channel"""
    if LOG_CHANNEL_ID == 0:
        return
    try:
        ch = guild.get_channel(LOG_CHANNEL_ID) or (await bot.fetch_channel(LOG_CHANNEL_ID))
        if ch:
            await ch.send(content=content, embed=embed)
    except Exception as e:
        print(f"⚠️ Could not send log to channel {LOG_CHANNEL_ID}: {e}")

def create_progress_bar(percentage, length=10):
    """Create a visual progress bar"""
    filled = int((percentage / 100) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage}%"

def calculate_wing_metrics(tasks):
    """Calculate metrics for a wing"""
    total = len(tasks)
    if total == 0:
        return {"total": 0, "done": 0, "in_progress": 0, "todo": 0, "completion_rate": 0}
    
    done = len([t for t in tasks if t[3] == "Done"])
    in_progress = len([t for t in tasks if t[3] == "InProgress"])
    todo = len([t for t in tasks if t[3] == "Todo"])
    completion_rate = int((done / total) * 100) if total > 0 else 0
    
    return {
        "total": total, "done": done, "in_progress": in_progress, 
        "todo": todo, "completion_rate": completion_rate
    }

def is_wing_master(member, wing_name=None):
    """Check if a member has wing master permissions"""
    if member.guild_permissions.administrator:
        return True
    
    for role in member.roles:
        role_name_lower = role.name.lower()
        if any(kw == role_name_lower for kw in MASTER_KEYWORDS):
            return True
        if wing_name and wing_name.lower() in role_name_lower:
            if any(kw in role_name_lower for kw in ["lead", "master", "head", "manager"]):
                return True
                
    return False
