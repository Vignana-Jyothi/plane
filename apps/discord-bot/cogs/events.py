import discord
from discord.ext import commands, tasks
import asyncio
import re
from datetime import datetime, timezone
from utils import apps_get, apps_post, send_log, send_reminder, create_progress_bar
from logic.wings import update_wing_showcase, update_task_message
from logic.permissions import sync_member_restrictions, ensure_category_restrictions
from config import SHADOW_MEMBER_ROLE_ID, MEMBER_ROLE_ID, APPSCRIPT_URL
from ui.components import RoleSelectionView, TaskActionView

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_all_showcases.start()
        self.check_intelligent_reminders.start()
        self.auto_process_delays.start()

    def cog_unload(self):
        self.update_all_showcases.cancel()
        self.check_intelligent_reminders.cancel()
        self.auto_process_delays.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Logged in as {self.bot.user}")
        try:
            synced = await self.bot.tree.sync()
            print(f"✅ Synced {len(synced)} commands.")
        except Exception as e: print(f"❌ Sync failed: {e}")

        # Start background tasks if not already running
        # done in __init__ for tasks.loop

        # Re-inject persistent views
        self.bot.add_view(TaskActionView())
        
        # Re-inject RoleSelectionView with dynamic roles
        options = []
        skip = ["vision", "member", "shadow member", "wing master", "app", "startup manager"]
        for guild in self.bot.guilds:
            for role in guild.roles:
                if role.name == "@everyone" or role.managed or role.permissions.administrator: continue
                if role.name.lower() in skip or role.is_bot_managed(): continue
                options.append(discord.SelectOption(label=role.name, value=str(role.id)))
                if len(options) >= 25: break
            if options: break # Just use one guild's roles or combine? Usually one guild for this bot.
            
        if options:
            self.bot.add_view(RoleSelectionView(options, MEMBER_ROLE_ID, SHADOW_MEMBER_ROLE_ID))
        
        print("✅ Persistent views re-injected.")

        # Sync missing members and perms
        for guild in self.bot.guilds:
            all_members = [m async for m in guild.fetch_members(limit=None)]
            await ensure_category_restrictions(guild, members_list=all_members)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if message.reference and message.reference.message_id:
            try:
                replied = await message.channel.fetch_message(message.reference.message_id)
                if replied.author == self.bot.user and replied.embeds:
                    footer = replied.embeds[0].footer.text
                    if footer and "ID:" in footer:
                        match = re.search(r"ID:\s*(\d+)", footer)
                        if match:
                            task_id = match.group(1); content = message.content.strip().lower()
                            payload = {"task_id": task_id, "updated_at": str(datetime.now(timezone.utc))}
                            action = ""
                            if content.isdigit() and 0 <= int(content) <= 100:
                                val = int(content)
                                payload["metric_current"] = content
                                action = f"Progress updated to {val}%"
                                if val == 100: payload["status"] = "Done"; action += " ✅"
                                elif val > 0: payload["status"] = "InProgress"
                            elif content in ["done", "completed", "finish"]:
                                payload["status"] = "Done"; payload["metric_current"] = "100"; action = "Task marked as Done ✅"
                            elif content in ["todo", "reset"]:
                                payload["status"] = "Todo"; payload["metric_current"] = "0"; action = "Task reset to Todo 📝"
                            elif content in ["progress", "doing", "wip"]:
                                payload["status"] = "InProgress"; action = "Task marked In Progress ⏳"
                            
                            if action:
                                await apps_post("TasksUpdate", payload, guild=message.guild)
                                await message.add_reaction("✅")
                                await message.reply(f"✅ {action}", delete_after=5)
                                if "metric_current" in payload: await update_task_message(message.guild, task_id, payload["metric_current"])
            except Exception as e: print(f"Error handling reply: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        new_roles = [r for r in after.roles if r not in before.roles]
        removed_roles = [r for r in before.roles if r not in after.roles]
        for role in new_roles:
            if role.id == SHADOW_MEMBER_ROLE_ID:
                await sync_member_restrictions(after, remove=False)
                await send_log(after.guild, f"🔒 Restricted **{after.mention}** (Shadow Member).")
            elif role.id in [MEMBER_ROLE_ID, SHADOW_MEMBER_ROLE_ID]:
                await apps_post("Members", [after.name, role.name, "Active"], guild=after.guild)
        for role in removed_roles:
            if role.id == SHADOW_MEMBER_ROLE_ID:
                await sync_member_restrictions(after, remove=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id: return
        channel = self.bot.get_channel(payload.channel_id)
        try:
            msg = await channel.fetch_message(payload.message_id)
            if msg.author == self.bot.user and msg.embeds:
                title = msg.embeds[0].title or ""
                if title.startswith("📅 Meeting:") and str(payload.emoji) == "✅":
                    rx = discord.utils.get(msg.reactions, emoji="✅")
                    if rx: await apps_post("MeetingsUpdate", {"message_id": str(msg.id), "attendee_count": rx.count - 1})
        except: pass

    @tasks.loop(hours=6)
    async def update_all_showcases(self):
        for guild in self.bot.guilds:
            data = await apps_get("WingShowcase", guild=guild)
            if data and len(data) > 1:
                for row in data[1:]: await update_wing_showcase(guild, row[0]); await asyncio.sleep(2)

    @tasks.loop(minutes=30)
    async def check_intelligent_reminders(self):
        for guild in self.bot.guilds:
            tasks_data = await apps_get("Tasks", guild=guild)
            if not tasks_data or len(tasks_data) < 2: continue

            # Fetch wing-specific reminder channels
            reminders_data = await apps_get("ReminderChannels", guild=guild)
            reminder_map = {}
            if reminders_data and len(reminders_data) > 1:
                # Column 0: wing_name, Column 1: channel_id
                for row in reminders_data[1:]:
                    if len(row) >= 2:
                        reminder_map[str(row[0])] = str(row[1])

            now = datetime.now(timezone.utc)
            for task in tasks_data[1:]:
                # task indices: 0:id, 1:title, 2:desc, 3:status, 6:assignee, 7:wing, 19:freq, 20:last_sent
                if len(task) < 4 or task[3] in ["Done", "Deleted"]: continue
                
                freq = int(task[19]) if len(task) > 19 and task[19] else 0
                if freq == 0: continue
                
                last = task[20] if len(task) > 20 else None
                should = False
                if not last: should = True
                else:
                    try:
                        lt = datetime.fromisoformat(str(last).replace('Z', '+00:00'))
                        if (now - lt).total_seconds() / 3600 >= freq: should = True
                    except: should = True
                
                if should:
                    wing_name = str(task[7]) if len(task) > 7 else None
                    target_channel_id = reminder_map.get(wing_name) if wing_name else None
                    
                    member = discord.utils.get(guild.members, name=task[6])
                    
                    embed = discord.Embed(
                        title=f"⏰ Task Reminder: {task[1]}",
                        description=f"This is an automated reminder for your task in **{wing_name or 'General'}**.",
                        color=discord.Color.orange(),
                        timestamp=now
                    )
                    embed.add_field(name="Task ID", value=f"`{task[0]}`", inline=True)
                    embed.add_field(name="Status", value=str(task[3]), inline=True)
                    if len(task) > 2 and task[2]:
                        embed.add_field(name="Details", value=str(task[2])[:1024], inline=False)
                    
                    await send_reminder(guild, content=member.mention if member else f"@{task[6]}", embed=embed, channel_id=target_channel_id)
                    await apps_post("TasksUpdate", {"task_id": task[0], "last_reminder_sent": str(now)})

    @tasks.loop(hours=24)
    async def auto_process_delays(self):
        await apps_post("ProcessDelaysAndScores", {"action": "auto_run"})

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
