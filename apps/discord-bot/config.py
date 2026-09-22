import os
import discord
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.getenv("DISCORD_TOKEN")
APPSCRIPT_URL = os.getenv("APPSCRIPT_URL")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0)) if os.getenv("LOG_CHANNEL_ID") else 0
REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID", LOG_CHANNEL_ID)) if os.getenv("REMINDER_CHANNEL_ID") else LOG_CHANNEL_ID

METRIC_TYPES = ["Percentage", "Count", "Custom"]
REMINDER_FREQUENCIES = {
    "Hourly": 1,
    "Every 6 Hours": 6,
    "Daily": 24,
    "Every 2 Days": 48,
    "Weekly": 168,
    "Custom": 0
}

# Role & Category Restrictions
MEMBER_ROLE_ID = 1465934768347811890
SHADOW_MEMBER_ROLE_ID = 1470359851187044464
WINGS_CATEGORY_ID = 1465934404126773362
SHADOW_WINGS_CATEGORY_ID = 1470360228909416679
COMMON_CATEGORY_ID = 1465934184865468564
PLANS_CATEGORY_ID = 1470358985990344766

# Wing Master Keywords
MASTER_KEYWORDS = ["wing master", "admin", "lead", "master", "head", "manager"]
