import discord
import asyncio # Added for asyncio.sleep
from config import WINGS_CATEGORY_ID, SHADOW_WINGS_CATEGORY_ID, COMMON_CATEGORY_ID, SHADOW_MEMBER_ROLE_ID, MEMBER_ROLE_ID
from bot_base import bot

async def sync_member_restrictions(member, remove=False, cats=None):
    """Helper to apply or remove restrictions for a specific member across categories"""
    is_shadow = any(r.id == SHADOW_MEMBER_ROLE_ID for r in member.roles)
    is_member = any(r.id == MEMBER_ROLE_ID for r in member.roles)
    
    if not is_shadow and not is_member:
        return

    # Use provided categories or fall back to guild cache
    wings_cat = cats.get('wings') if cats else member.guild.get_channel(WINGS_CATEGORY_ID)
    shadow_wings_cat = cats.get('shadow') if cats else member.guild.get_channel(SHADOW_WINGS_CATEGORY_ID)
    common_cat = cats.get('common') if cats else member.guild.get_channel(COMMON_CATEGORY_ID)

    async def apply_policy(category, allow, reason_prefix):
        if not category or not isinstance(category, discord.CategoryChannel): return
        try:
            current_ovr = category.overwrites.get(member)
            if remove:
                if current_ovr: await category.set_permissions(member, overwrite=None)
                for ch in category.channels:
                    if ch.overwrites.get(member): await ch.set_permissions(member, overwrite=None)
            elif allow:
                # To ALLOW, we remove any user-specific blocks/overwrites.
                # This lets role-based permissions take over correctly.
                if current_ovr:
                    await category.set_permissions(member, overwrite=None, reason=f"{reason_prefix} Reverting to Role")
                
                for ch in category.channels:
                    if ch.overwrites.get(member):
                        await ch.set_permissions(member, overwrite=None, reason=f"{reason_prefix} Clearing channel block")
            else:
                # To RESTRICT, we apply a hard user-specific block on category AND all channels.
                if not current_ovr or current_ovr.view_channel != False:
                    await category.set_permissions(member, view_channel=False, reason=f"{reason_prefix} Restricted")
                
                for ch in category.channels:
                    ch_ovr = ch.overwrites.get(member)
                    if not ch_ovr or ch_ovr.view_channel != False:
                        await ch.set_permissions(member, view_channel=False, reason=f"{reason_prefix} Restricted Channel")
        except: pass

    if is_shadow: await apply_policy(wings_cat, allow=False, reason_prefix="Shadow Member")
    elif is_member: await apply_policy(wings_cat, allow=True, reason_prefix="Member")

    # Policy 2: Shadow Wings Category (Both Allowed)
    if is_member or is_shadow: await apply_policy(shadow_wings_cat, allow=True, reason_prefix="Wings Access")

    if common_cat:
        try:
            if remove:
                if common_cat.overwrites.get(member): await common_cat.set_permissions(member, overwrite=None)
            elif is_shadow or is_member:
                # Wipe any user-specific overwrite on common category to rely on server defaults/roles
                if common_cat.overwrites.get(member):
                    await common_cat.set_permissions(member, overwrite=None)
        except: pass

async def ensure_category_restrictions(guild_to_sync=None, members_list=None):
    """Ensure Shadow Members and Members have correct category access."""
    guilds = [guild_to_sync] if guild_to_sync else bot.guilds
    for guild in guilds:
        # Pre-fetch categories
        cats = {
            'wings': guild.get_channel(WINGS_CATEGORY_ID) or await bot.fetch_channel(WINGS_CATEGORY_ID),
            'shadow': guild.get_channel(SHADOW_WINGS_CATEGORY_ID) or await bot.fetch_channel(SHADOW_WINGS_CATEGORY_ID),
            'common': guild.get_channel(COMMON_CATEGORY_ID) or await bot.fetch_channel(COMMON_CATEGORY_ID)
        }
        
        target_members = []
        if members_list:
            target_members = [m for m in members_list if any(r.id in [SHADOW_MEMBER_ROLE_ID, MEMBER_ROLE_ID] for r in m.roles)]
        else:
            async for member in guild.fetch_members(limit=None):
                if any(r.id in [SHADOW_MEMBER_ROLE_ID, MEMBER_ROLE_ID] for r in member.roles):
                    target_members.append(member)
        
        print(f"🔒 Syncing {len(target_members)} Members policies in {guild.name}...", flush=True)
        for member in target_members:
            try:
                await sync_member_restrictions(member, cats=cats)
                await asyncio.sleep(0.3) # Balance speed and rate limits
            except: pass
        print(f"✅ Finished syncing {guild.name}", flush=True)
