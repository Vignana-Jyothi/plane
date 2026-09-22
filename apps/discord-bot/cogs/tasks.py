import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime, timezone
from utils import apps_get, is_wing_master, apps_post, create_progress_bar
from ui.components import TaskMetricsModal, ProgressUpdateModal, TaskActionView, DelegateTaskView
from bot_base import bot

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createtask", description="Create a new task with progress metrics")
    async def create_task(self, interaction: discord.Interaction, wing: discord.Role, person: Optional[discord.Member] = None, collaborator: Optional[discord.Role] = None, reminder: int = 48, target_id: Optional[str] = None):
        if person and person.bot: return await interaction.response.send_message("❌ Cannot assign to bots.", ephemeral=True)
        await interaction.response.send_modal(TaskMetricsModal(wing.name, person, "Task", collaborator, reminder, target_id or ""))

    @app_commands.command(name="creategoal", description="Create a weekly or monthly goal")
    @app_commands.choices(goal_type=[app_commands.Choice(name="Weekly", value="Weekly"), app_commands.Choice(name="Monthly", value="Monthly")])
    async def create_goal(self, interaction: discord.Interaction, goal_type: str, wing: discord.Role, person: Optional[discord.Member] = None, reminder: int = 24):
        if person and person.bot: return await interaction.response.send_message("❌ Cannot assign to bots.", ephemeral=True)
        if not is_wing_master(interaction.user, wing.name):
             return await interaction.response.send_message(f"❌ Restricted to Wing Masters or {wing.name} Leads.", ephemeral=True)
        await interaction.response.send_modal(TaskMetricsModal(wing.name, person, goal_type, None, reminder))

    @app_commands.command(name="mytasks", description="View your current tasks")
    async def my_tasks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        rows = await apps_get("Tasks")
        if not rows or len(rows) < 2: return await interaction.followup.send("No tasks found.")
        username = interaction.user.name.lower()
        user_tasks = [r for r in rows[1:] if len(r) > 6 and r[3] not in ["Done", "Deleted"] and str(r[6]).lower() == username]
        
        if not user_tasks:
            embed = discord.Embed(
                title=f"📋 My Active Tasks: {interaction.user.name}", 
                color=discord.Color.from_rgb(88, 101, 242),
                description="🎉 **You're all caught up!** No active tasks found."
            )
            return await interaction.followup.send(embed=embed)

        await interaction.followup.send(f"📋 Found **{len(user_tasks)}** active tasks for you. Showing the top 5:")

        for t in user_tasks[:5]:
            tid = str(t[0]); title = t[1]; status = t[3]; desc = t[2]
            deadline = t[4] if len(t) > 4 else "No deadline"
            wing = t[7] if len(t) > 7 else "General"
            priority = t[8] if len(t) > 8 else "Medium"
            
            status_emoji = "✅" if status == "Done" else "⏳" if status == "InProgress" else "📝"
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
            color_map = {"High": discord.Color.red(), "Medium": discord.Color.gold(), "Low": discord.Color.green()}
            
            embed = discord.Embed(title=f"🎯 {title}", description=desc, color=color_map.get(priority, discord.Color.blue()))
            embed.add_field(name="Status", value=f"{status_emoji} {status}", inline=True)
            embed.add_field(name="Priority", value=f"{priority_emoji} {priority}", inline=True)
            embed.add_field(name="Wing", value=wing, inline=True)
            embed.add_field(name="Deadline", value=deadline, inline=True)
            
            if len(t) > 16 and t[15] == "Percentage" and t[16]:
                try:
                    percentage = int(t[16])
                    embed.add_field(name="📊 Progress", value=create_progress_bar(percentage, 10), inline=False)
                except: pass
            
            embed.set_footer(text=f"ID: {tid} • Created {t[10][:10] if len(t) > 10 else 'N/A'}")
            await interaction.channel.send(embed=embed, view=TaskActionView(tid, wing))

    @app_commands.command(name="delegate", description="Delegate a task to another user")
    async def delegate_task(self, interaction: discord.Interaction, task_id: str, user: discord.Member):
        if user.bot: return await interaction.response.send_message("❌ Cannot delegate to bots.", ephemeral=True)
        await interaction.response.defer()
        payload = {"task_id": task_id, "assignee": user.name, "updated_at": str(datetime.now(timezone.utc))}
        if await apps_post("TasksUpdate", payload, guild=interaction.guild):
            from logic.wings import update_task_message
            await update_task_message(interaction.guild, task_id, None)
            
            import asyncio
            asyncio.create_task(apps_post("ProcessDelaysAndScores", {"action": "run"}))
            
            # Fetch task title for better logging
            task_title = "Unknown Task"
            try:
                tasks_data = await apps_get("Tasks", guild=interaction.guild)
                task = next((t for t in tasks_data[1:] if str(t[0]) == str(task_id)), None)
                if task: task_title = task[1]
            except: pass
            
            await interaction.followup.send(f"✅ Task **{task_title}** delegated to {user.mention}!")
            from utils import send_log
            await send_log(interaction.guild, f"🔄 Task **{task_title}** (`{task_id}`) delegated to {user.mention} by {interaction.user.mention}")

    @app_commands.command(name="board", description="View the Kanban board for a wing")
    async def board(self, interaction: discord.Interaction, wing: Optional[discord.Role] = None):
        await interaction.response.defer()
        rows = await apps_get("Tasks", wing=wing.name if wing else None)
        if not rows or len(rows) < 2: return await interaction.followup.send("No tasks found.")
        
        buckets = {"Todo": [], "InProgress": [], "Done": []}
        for t in rows[1:]:
            if len(t) < 8: continue
            if wing and t[7] != wing.name: continue
            status_raw = str(t[3])
            if status_raw == "Deleted": continue
            
            tid = str(t[0]); title = t[1]; assignee = t[6]
            priority = t[8] if len(t) > 8 else "Medium"
            wing_name = t[7]
            
            p_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
            progress = ""
            if len(t) > 16 and t[15] == "Percentage" and t[16]: progress = f" [{t[16]}%]"
            
            target_ind = f" (Ref: `{t[22]}`)" if len(t) > 22 and t[22] else ""
            line = f"{p_emoji} `{tid}` {title}{progress}{target_ind} — **@{assignee}** [{wing_name}]"
            
            status_norm = status_raw.replace(" ", "")
            target_key = "Todo"
            if status_norm in buckets: target_key = status_norm
            elif "done" in status_norm.lower() or "complete" in status_norm.lower(): target_key = "Done"
            elif "progress" in status_norm.lower(): target_key = "InProgress"
            
            buckets[target_key].append(line)

        title_text = f"📋 Kanban Board - {wing.name}" if wing else "📋 Kanban Board (All Wings)"
        embed = discord.Embed(title=title_text, color=discord.Color.from_rgb(114, 137, 218))
        for k in ["Todo", "InProgress", "Done"]:
            items = buckets.get(k, ["*(No tasks)*"])
            emoji = "📝" if k == "Todo" else "⏳" if k == "InProgress" else "✅"
            embed.add_field(name=f"{emoji} {k}", value="\n".join(items[:12])[:1024], inline=False)
        
        embed.set_footer(text=f"Total Tasks: {len(rows)-1}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="viewtasks", description="View tasks of another member")
    async def view_tasks(self, interaction: discord.Interaction, user: discord.Member):
        if user.bot: return await interaction.response.send_message("❌ Bots don't have tasks.", ephemeral=True)
        await interaction.response.defer()
        rows = await apps_get("Tasks")
        if not rows or len(rows) < 2: return await interaction.followup.send("No tasks found.")
        username = user.name.lower()
        user_tasks = [r for r in rows[1:] if len(r) > 6 and r[3] not in ["Done", "Deleted"] and ((len(r) > 5 and str(r[5]).lower() == username) or (str(r[6]).lower() == username))]
        
        if not user_tasks:
            embed = discord.Embed(
                title=f"📋 Active Tasks: {user.display_name}", 
                color=discord.Color.from_rgb(88, 101, 242),
                description=f"🎉 **{user.display_name} is all caught up!** No active tasks found."
            )
            return await interaction.followup.send(embed=embed)

        await interaction.followup.send(f"📋 Found **{len(user_tasks)}** active tasks for **{user.display_name}**. Showing the top 5:")

        for t in user_tasks[:5]:
            tid = str(t[0]); title = t[1]; status = t[3]; desc = t[2]
            deadline = t[4] if len(t) > 4 else "No deadline"
            wing = t[7] if len(t) > 7 else "General"
            priority = t[8] if len(t) > 8 else "Medium"
            
            status_emoji = "✅" if status == "Done" else "⏳" if status == "InProgress" else "📝"
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
            color_map = {"High": discord.Color.red(), "Medium": discord.Color.gold(), "Low": discord.Color.green()}
            
            embed = discord.Embed(title=f"🎯 {title}", description=desc, color=color_map.get(priority, discord.Color.blue()))
            embed.add_field(name="Status", value=f"{status_emoji} {status}", inline=True)
            embed.add_field(name="Priority", value=f"{priority_emoji} {priority}", inline=True)
            embed.add_field(name="Wing", value=wing, inline=True)
            embed.add_field(name="Deadline", value=deadline, inline=True)
            
            if len(t) > 16 and t[15] == "Percentage" and t[16]:
                try:
                    percentage = int(t[16])
                    embed.add_field(name="📊 Progress", value=create_progress_bar(percentage, 10), inline=False)
                except: pass
            
            embed.set_footer(text=f"ID: {tid} • Created {t[10][:10] if len(t) > 10 else 'N/A'}")
            await interaction.channel.send(embed=embed, view=TaskActionView(tid, wing))

    @app_commands.command(name="addweeklytarget", description="Add a new weekly target for a wing")
    async def add_weekly_target(self, interaction: discord.Interaction, wing: discord.Role, person: Optional[discord.Member] = None, reminder: int = 24):
        if not is_wing_master(interaction.user, wing.name):
            return await interaction.response.send_message(f"❌ Restricted to Wing Masters or {wing.name} Leads.", ephemeral=True)
        await interaction.response.send_modal(TaskMetricsModal(wing.name, person, "Weekly", None, reminder))

    @app_commands.command(name="addmonthlytarget", description="Add a new monthly target for a wing")
    async def add_monthly_target(self, interaction: discord.Interaction, wing: discord.Role, person: Optional[discord.Member] = None, reminder: int = 24):
        if not is_wing_master(interaction.user, wing.name):
            return await interaction.response.send_message(f"❌ Restricted to Wing Masters or {wing.name} Leads.", ephemeral=True)
        await interaction.response.send_modal(TaskMetricsModal(wing.name, person, "Monthly", None, reminder))

    @app_commands.command(name="createplan", description="Create a strategic plan with milestones")
    async def create_plan(self, interaction: discord.Interaction, wing: discord.Role, person: Optional[discord.Member] = None):
        if not is_wing_master(interaction.user, wing.name):
            return await interaction.response.send_message(f"❌ Restricted to Wing Masters or {wing.name} Leads.", ephemeral=True)
        await interaction.response.send_modal(TaskMetricsModal(wing.name, person, "Plan", None, 168))

    @app_commands.command(name="updateprogress", description="Update progress on a task")
    async def update_progress(self, interaction: discord.Interaction, task_id: str):
        try:
            # We don't defer here because we want to send a modal.
            # We use a fast timeout for the Apps Script call of 2 seconds.
            import asyncio
            data = await asyncio.wait_for(apps_get("Tasks"), timeout=2.5)
            task = next((t for t in data[1:] if str(t[0]) == task_id), None)
            if not task: return await interaction.response.send_message("❌ Task not found.", ephemeral=True)
            
            # Modal params: task_id, metric_type, current, total, task_title
            await interaction.response.send_modal(ProgressUpdateModal(task_id, task[15], task[16], task[17], task[1]))
        except asyncio.TimeoutError:
            await interaction.response.send_message("⚠️ The database is responding slowly. Please try again in a moment.", ephemeral=True)
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="deletetask", description="Delete a task you created")
    async def delete_task(self, interaction: discord.Interaction, task_id: str):
        await interaction.response.defer(ephemeral=True)
        data = await apps_get("Tasks")
        task = next((t for t in data[1:] if str(t[0]) == task_id), None)
        if not task: return await interaction.followup.send("❌ Task not found.", ephemeral=True)
        if interaction.user.name != task[5] and not is_wing_master(interaction.user, task[7]):
            return await interaction.followup.send("❌ Unauthorized.", ephemeral=True)
        if await apps_post("TasksUpdate", {"task_id": task_id, "status": "Deleted", "updated_at": str(datetime.now(timezone.utc))}, guild=interaction.guild):
            await interaction.followup.send("✅ Task deleted.", ephemeral=True)

    @app_commands.command(name="deletetarget", description="Delete a weekly or monthly target")
    async def delete_target(self, interaction: discord.Interaction, target_id: str):
        await self.delete_task(interaction, target_id)

async def setup(bot):
    await bot.add_cog(TasksCog(bot))
