import discord
import asyncio
from datetime import datetime, timezone
from utils import apps_post, apps_get, send_log, create_progress_bar, is_wing_master
from logic.wings import update_task_message, update_wing_showcase

class ProgressUpdateModal(discord.ui.Modal, title="Update Task Progress"):
    new_progress = discord.ui.TextInput(
        label="New Progress Value",
        placeholder="e.g., 75 (for percentage) or 8 (for count)",
        max_length=10,
        required=True
    )
    
    notes = discord.ui.TextInput(
        label="Update Notes (Optional)",
        style=discord.TextStyle.paragraph,
        placeholder="What progress was made?",
        max_length=500,
        required=False
    )

    def __init__(self, task_id: str, current_metric_type: str, current_value: str, total_value: str = "", task_title: str = "Unknown Task"):
        super().__init__()
        self.task_id = task_id
        self.metric_type = current_metric_type
        self.current_value = current_value
        self.total_value = total_value
        self.task_title = task_title

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            return
        
        new_val = self.new_progress.value.strip()
        payload = {
            "task_id": self.task_id,
            "metric_current": new_val,
            "updated_at": str(datetime.now(timezone.utc))
        }
        result = await apps_post("TasksUpdate", payload, guild=interaction.guild)
        
        if not result:
            return await interaction.followup.send("❌ Failed to update progress.", ephemeral=True)
        
        progress_display = ""
        if self.metric_type == "Percentage":
            try:
                percentage = int(new_val)
                progress_display = create_progress_bar(percentage)
            except:
                progress_display = f"{new_val}%"
        elif self.metric_type == "Count":
            progress_display = f"{new_val}/{self.total_value} items"
        else:
            progress_display = new_val
        
        embed = discord.Embed(
            title="📊 Progress Updated",
            description=f"Task ID: {self.task_id}",
            color=discord.Color.green()
        )
        embed.add_field(name="New Progress", value=progress_display, inline=False)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)
        embed.set_footer(text=f"Updated by {interaction.user.name}")
        
        await interaction.followup.send(embed=embed)
        await send_log(interaction.guild, f"📊 Progress updated for task **{self.task_title}** (`{self.task_id}`) by {interaction.user.mention}")
        asyncio.create_task(update_task_message(interaction.guild, self.task_id, new_val))

class DelegateUserSelect(discord.ui.UserSelect):
    def __init__(self, task_id: str, wing_name: str):
        super().__init__(placeholder="Select a user to delegate this task to...", min_values=1, max_values=1)
        self.task_id = task_id
        self.wing_name = wing_name

    async def callback(self, interaction: discord.Interaction):
        target_user = self.values[0]
        if target_user.bot:
            return await interaction.response.send_message("❌ You cannot delegate tasks to bots.", ephemeral=True)

        has_wing_role = any(role.name.lower() == self.wing_name.lower() for role in target_user.roles)
        if not has_wing_role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(f"❌ **{target_user.display_name}** does not have the **{self.wing_name}** role.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        payload = {
            "task_id": self.task_id,
            "assignee": target_user.name,
            "updated_at": str(datetime.now(timezone.utc))
        }
        result = await apps_post("TasksUpdate", payload, guild=interaction.guild)
        if result:
            await update_task_message(interaction.guild, self.task_id, None)
            
            # Get task title for better logging
            task_title = getattr(self.view, 'task_title', "Unknown Task")
            if task_title == "Unknown Task":
                try:
                    tasks_data = await apps_get("Tasks", guild=interaction.guild)
                    task = next((t for t in tasks_data[1:] if str(t[0]) == str(self.task_id)), None)
                    if task: task_title = task[1]
                except: pass
            
            await interaction.followup.send(f"✅ Task **{task_title}** successfully delegated to {target_user.mention}.", ephemeral=True)
            await send_log(interaction.guild, f"🤝 Task **{task_title}** (`{self.task_id}`) delegated to {target_user.mention} by {interaction.user.mention}")
        else:
            await interaction.followup.send("❌ Failed to delegate task. Please try again.", ephemeral=True)

class DelegateTaskView(discord.ui.View):
    def __init__(self, task_id: str, wing_name: str, task_title: str = "Unknown Task"):
        super().__init__(timeout=60)
        self.task_title = task_title
        self.add_item(DelegateUserSelect(task_id, wing_name))

    async def on_timeout(self):
        # We don't really need to do much on timeout for this ephemeral view
        pass

class TaskActionView(discord.ui.View):
    def __init__(self, task_id: str = None, wing_name: str = None):
        super().__init__(timeout=None)
        self.task_id = task_id
        self.wing_name = wing_name

    def get_task_id(self, interaction: discord.Interaction):
        if self.task_id: return self.task_id
        try:
            footer = interaction.message.embeds[0].footer.text
            return footer.split(":")[1].split("•")[0].strip()
        except: return None

    async def check_permissions(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator: return True
        try:
            embed = interaction.message.embeds[0]
            owner_mention = ""
            assignee_mention = ""
            for field in embed.fields:
                if field.name == "Owner": owner_mention = field.value
                elif field.name == "Assigned To": assignee_mention = field.value
            user_mention = interaction.user.mention
            if user_mention == owner_mention or user_mention == assignee_mention: return True
        except: pass
        wing = self.wing_name
        if not wing:
            try:
                for field in interaction.message.embeds[0].fields:
                    if field.name == "Wing": wing = field.value; break
            except: pass
        if wing and is_wing_master(interaction.user, wing): return True
        return False

    @discord.ui.button(label="In Progress", style=discord.ButtonStyle.secondary, emoji="⏳", custom_id="task_btn_progress")
    async def set_in_progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return await interaction.response.send_message("❌ Permissions denied.", ephemeral=True)
        tid = self.get_task_id(interaction)
        if not tid: return await interaction.response.send_message("❌ Task ID not found.", ephemeral=True)
        
        # Get title for logging
        task_title = "Unknown Task"
        try:
            embed_title = interaction.message.embeds[0].title
            task_title = embed_title.split(":", 1)[1].strip() if ":" in embed_title else embed_title
        except: pass

        await interaction.response.defer(ephemeral=True)
        payload = {"task_id": tid, "status": "InProgress", "updated_at": str(datetime.now(timezone.utc))}
        if await apps_post("TasksUpdate", payload, guild=interaction.guild):
            await update_task_message(interaction.guild, tid, None)
            await interaction.followup.send(f"✅ Task **{task_title}** marked as **In Progress**.", ephemeral=True)
            await send_log(interaction.guild, f"🔁 Task **{task_title}** (`{tid}`) moved to **In Progress** by {interaction.user.mention}")

    @discord.ui.button(label="Mark Done", style=discord.ButtonStyle.success, emoji="✅", custom_id="task_btn_done")
    async def set_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return await interaction.response.send_message("❌ Permissions denied.", ephemeral=True)
        tid = self.get_task_id(interaction)
        if not tid: return await interaction.response.send_message("❌ Task ID not found.", ephemeral=True)
        
        # Get title for logging
        task_title = "Unknown Task"
        try:
            embed_title = interaction.message.embeds[0].title
            task_title = embed_title.split(":", 1)[1].strip() if ":" in embed_title else embed_title
        except: pass

        await interaction.response.defer(ephemeral=True)
        payload = {"task_id": tid, "status": "Done", "metric_current": "100", "updated_at": str(datetime.now(timezone.utc))}
        if await apps_post("TasksUpdate", payload, guild=interaction.guild):
            await update_task_message(interaction.guild, tid, "100")
            await interaction.followup.send(f"✅ Task **{task_title}** marked as **Done**!", ephemeral=True)
            await send_log(interaction.guild, f"🎉 Task **{task_title}** (`{tid}`) completed by {interaction.user.mention}")
            wing = self.wing_name
            if not wing:
                try:
                    for field in interaction.message.embeds[0].fields:
                        if field.name == "Wing": wing = field.value; break
                except: pass
            if wing: asyncio.create_task(update_wing_showcase(interaction.guild, wing))

    @discord.ui.button(label="Update %", style=discord.ButtonStyle.primary, emoji="📊", custom_id="task_btn_update")
    async def update_val(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return await interaction.response.send_message("❌ Permissions denied.", ephemeral=True)
        tid = self.get_task_id(interaction)
        if not tid: return await interaction.response.send_message("❌ Task ID not found.", ephemeral=True)
        tasks_data = await apps_get("Tasks", wing=self.wing_name, guild=interaction.guild)
        task = next((t for t in tasks_data[1:] if str(t[0]) == str(tid)), None)
        if task:
            metric_type = task[15] if len(task) > 15 else "None"
            metric_current = task[16] if len(task) > 16 else "0"
            metric_total = task[17] if len(task) > 17 else ""
            task_title = task[1] if len(task) > 1 else "Unknown Task"
            await interaction.response.send_modal(ProgressUpdateModal(tid, metric_type, metric_current, metric_total, task_title))
        else: await interaction.response.send_message("❌ Task not found.", ephemeral=True)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="task_btn_delete")
    async def delete_task_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return await interaction.response.send_message("❌ Permissions denied.", ephemeral=True)
        tid = self.get_task_id(interaction)
        if not tid: return await interaction.response.send_message("❌ Task ID not found.", ephemeral=True)
        
        # Get title for logging
        task_title = "Unknown Task"
        try:
            embed_title = interaction.message.embeds[0].title
            task_title = embed_title.split(":", 1)[1].strip() if ":" in embed_title else embed_title
        except: pass

        await interaction.response.defer(ephemeral=True)
        payload = {"task_id": tid, "status": "Deleted", "updated_at": str(datetime.now(timezone.utc))}
        if await apps_post("TasksUpdate", payload, guild=interaction.guild):
            await interaction.message.delete()
            await interaction.followup.send(f"✅ Task **{task_title}** deleted successfully.", ephemeral=True)
            await send_log(interaction.guild, f"🗑️ Task **{task_title}** (`{tid}`) deleted by {interaction.user.mention}")

    @discord.ui.button(label="Delegate", style=discord.ButtonStyle.secondary, emoji="🤝", custom_id="task_btn_delegate")
    async def delegate_task_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return await interaction.response.send_message("❌ Permissions denied.", ephemeral=True)
        tid = self.get_task_id(interaction)
        if not tid: return await interaction.response.send_message("❌ Task ID not found.", ephemeral=True)
        
        # Get title for passing to DelegateTaskView
        task_title = "Unknown Task"
        try:
            embed_title = interaction.message.embeds[0].title
            task_title = embed_title.split(":", 1)[1].strip() if ":" in embed_title else embed_title
        except: pass

        wing = self.wing_name
        if not wing:
            try:
                for field in interaction.message.embeds[0].fields:
                    if field.name == "Wing": wing = field.value; break
            except: pass
        await interaction.response.send_message(f"Select the new assignee for **{task_title}**:", view=DelegateTaskView(tid, wing or "General", task_title), ephemeral=True)

class TeamRoleSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose your Wing/Team...", min_values=1, max_values=1, options=options, custom_id="team_role_select")
        
    async def callback(self, interaction: discord.Interaction):
        wing_ids = [int(opt.value) for opt in self.options]
        if any(r.id in wing_ids for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Wing already selected.", ephemeral=True)
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        try:
            if role:
                await interaction.user.add_roles(role); await interaction.response.send_message(f"✅ Joined **{role.name}**!", ephemeral=True)
            else: await interaction.response.send_message("❌ Role not found.", ephemeral=True)
        except discord.errors.Forbidden:
            await interaction.response.send_message("❌ Lacking permissions.", ephemeral=True)

class BaseRoleSelect(discord.ui.Select):
    def __init__(self, member_role_id, shadow_role_id):
        options = [
            discord.SelectOption(label="Member", value=str(member_role_id), description="Join as a Member", emoji="👤"),
            discord.SelectOption(label="Shadow Member", value=str(shadow_role_id), description="Join as a Shadow Member", emoji="👥")
        ]
        super().__init__(placeholder="Select Member Type...", min_values=1, max_values=1, options=options, custom_id="base_role_select")

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        if any(r.id in [int(self.options[0].value), int(self.options[1].value)] for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Role already selected.", ephemeral=True)
        try:
            if role:
                await interaction.user.add_roles(role); await interaction.response.send_message(f"✅ Assigned **{role.name}**!", ephemeral=True)
            else: await interaction.response.send_message("❌ Role not found.", ephemeral=True)
        except discord.errors.Forbidden:
            await interaction.response.send_message("❌ Lacking permissions.", ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, wing_options, member_role_id, shadow_role_id):
        super().__init__(timeout=None)
        self.add_item(BaseRoleSelect(member_role_id, shadow_role_id))
        if len(wing_options) > 0: self.add_item(TeamRoleSelect(wing_options))

class MeetingModal(discord.ui.Modal, title="Schedule Meeting"):
    agenda = discord.ui.TextInput(label="Meeting Title/Agenda", style=discord.TextStyle.paragraph, max_length=200, required=True)
    description = discord.ui.TextInput(label="Details", style=discord.TextStyle.paragraph, max_length=500, required=False)
    scheduled_time = discord.ui.TextInput(label="Date & Time (YYYY-MM-DD HH:MM 24hr)", max_length=20, required=True)
    duration_minutes = discord.ui.TextInput(label="Duration (minutes)", max_length=10, required=True)

    def __init__(self, role: discord.Role):
        super().__init__(); self.role = role

    async def on_submit(self, interaction: discord.Interaction):
        try: await interaction.response.defer()
        except: return
        try: dur_mins = int(self.duration_minutes.value)
        except: return await interaction.followup.send("❌ Invalid duration.", ephemeral=True)
        try:
            parsed_time = datetime.strptime(self.scheduled_time.value.strip(), "%Y-%m-%d %H:%M")
            parsed_time = parsed_time.replace(tzinfo=timezone.utc)
        except: return await interaction.followup.send("❌ Invalid date/time format.", ephemeral=True)
        meeting_id = int(datetime.now(timezone.utc).timestamp() * 1000)
        hours = dur_mins // 60
        mins = dur_mins % 60
        duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        timestamp_full = f"<t:{int(parsed_time.timestamp())}:F>"
        embed = discord.Embed(title=f"📅 Meeting: {self.agenda.value}", description=self.description.value or "No details", color=discord.Color.blue())
        embed.add_field(name="Wing/Group", value=self.role.mention, inline=True)
        embed.add_field(name="📅 When", value=timestamp_full, inline=False)
        embed.add_field(name="⏱️ Duration", value=duration_str, inline=True)
        meeting_msg = await interaction.channel.send(content=self.role.mention, embed=embed)
        await meeting_msg.add_reaction("✅")
        row = [meeting_id, self.role.name, self.agenda.value, self.description.value or "", str(parsed_time), duration_str, interaction.user.name, str(datetime.now(timezone.utc)), 0, "", str(meeting_msg.id), "scheduled"]
        await apps_post("Meetings", row, guild=interaction.guild)
        await interaction.followup.send("✅ Meeting scheduled!", ephemeral=True)
        await send_log(interaction.guild, f"📅 Meeting scheduled by {interaction.user.mention}: **{self.agenda.value}**")

class TaskMetricsModal(discord.ui.Modal, title="Create Task with Metrics"):
    task_title = discord.ui.TextInput(label="Task Title", max_length=100, required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000, required=True)
    deadline = discord.ui.TextInput(label="Deadline (YYYY-MM-DD)", max_length=10, required=False)
    priority = discord.ui.TextInput(label="Priority (High/Medium/Low)", max_length=10, required=False)
    metric_info = discord.ui.TextInput(label="Metrics (e.g., Percentage:0)", max_length=50, required=False)

    def __init__(self, wing_name: str, assignee: discord.Member = None, task_type: str = "Task", collaborator: discord.Role = None, reminder_hours: int = 48, parent_id: str = ""):
        super().__init__()
        self.wing_name = wing_name; self.assignee = assignee; self.task_type = task_type
        self.collaborator = collaborator; self.reminder_hours = reminder_hours; self.parent_id = parent_id

    async def on_submit(self, interaction: discord.Interaction):
        try: await interaction.response.defer()
        except: return
        task_id = int(datetime.now(timezone.utc).timestamp() * 1000)
        status = "Todo"; created = str(datetime.now(timezone.utc))
        deadline_val = self.deadline.value.strip() if self.deadline.value and self.deadline.value.strip().lower() != "none" else ""
        priority_val = self.priority.value.strip().title() if self.priority.value else "Medium"
        if priority_val not in ["High", "Medium", "Low"]: priority_val = "Medium"
        target_assignee = self.assignee
        if not target_assignee:
            wing_master_role_id = 1468504967844462692
            wing_role = discord.utils.get(interaction.guild.roles, name=self.wing_name)
            found_master = None
            if wing_role:
                for member in wing_role.members:
                    if not member.bot and any(r.id == wing_master_role_id for r in member.roles):
                        found_master = member; break
            target_assignee = found_master or interaction.user
        
        has_wing_role = False
        if self.wing_name and hasattr(target_assignee, 'roles'):
            has_wing_role = any(role.name.lower() == self.wing_name.lower() for role in target_assignee.roles)
        
        wing_role_exists = discord.utils.get(interaction.guild.roles, name=self.wing_name) if self.wing_name else None
        if wing_role_exists and not has_wing_role and not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send(f"❌ Assignee missing wing role.", ephemeral=True)
        assignee_val = target_assignee.mention; assignee_name = target_assignee.name
        collab_val = self.collaborator.name if self.collaborator else ""
        metric_type = "None"; metric_current = ""; metric_total = ""; metric_unit = ""
        if self.metric_info.value:
            parts = self.metric_info.value.split(":"); metric_type = parts[0].strip().title()
            if metric_type == "Percentage": metric_current = parts[1].strip(); metric_total = "100"; metric_unit = "%"
            elif metric_type == "Count" and "/" in parts[1]:
                cp = parts[1].split("/"); metric_current = cp[0].strip(); metric_total = cp[1].strip(); metric_unit = "items"
        row = [task_id, self.task_title.value, self.description.value, status, deadline_val, interaction.user.name, assignee_name, self.wing_name, priority_val, "", created, "", self.task_type, collab_val, "", metric_type, metric_current, metric_total, metric_unit, self.reminder_hours, "", "", self.parent_id, str(interaction.channel.id)]
        if await apps_post("Tasks", row, guild=interaction.guild):
            color_map = {"High": discord.Color.red(), "Medium": discord.Color.gold(), "Low": discord.Color.green()}
            embed = discord.Embed(title=f"🎯 {self.task_type}: {self.task_title.value}", description=self.description.value, color=color_map.get(priority_val, discord.Color.gold()))
            if metric_type == "Percentage" and metric_current: embed.add_field(name="📊 Progress", value=create_progress_bar(int(metric_current)), inline=False)
            embed.add_field(name="Owner", value=interaction.user.mention, inline=True)
            embed.add_field(name="Assigned To", value=assignee_val, inline=True)
            
            # Find showcase channel for special task types
            target_channel = interaction.channel
            if self.task_type in ["Weekly", "Monthly", "Plan"]:
                sc = await apps_get("WingShowcase", guild=interaction.guild)
                if sc and len(sc) > 1:
                    for r in sc[1:]:
                        if r[0] == self.wing_name and len(r) > 1 and r[1]:
                            try:
                                found_ch = interaction.guild.get_channel(int(r[1])) or await bot.fetch_channel(int(r[1]))
                                if found_ch:
                                    target_channel = found_ch
                                    break
                            except: continue
            
            embed.set_footer(text=f"ID: {task_id} • Created {created[:10]}")
            msg = await target_channel.send(embed=embed)
            await apps_post("TasksUpdate", {"task_id": task_id, "message_id": str(msg.id)})
            await msg.edit(view=TaskActionView(str(task_id), self.wing_name))
            await interaction.followup.send(f"✅ {self.task_type} created in {target_channel.mention}!", ephemeral=True)
            await send_log(interaction.guild, f"➕ New {self.task_type} created: **{self.task_title.value}** (ID: `{task_id}`)")
            asyncio.create_task(update_wing_showcase(interaction.guild, self.wing_name))

class VisionPlanModal(discord.ui.Modal):
    vision_statement = discord.ui.TextInput(label="Vision Statement", style=discord.TextStyle.paragraph, max_length=500, required=True)
    targets = discord.ui.TextInput(label="Specific Targets", style=discord.TextStyle.paragraph, max_length=1000, required=True)

    def __init__(self, wing_name: str, plan_type: str):
        super().__init__(title=f"Set {plan_type} Vision Plan: {wing_name}")
        self.wing_name = wing_name; self.plan_type = plan_type

    async def on_submit(self, interaction: discord.Interaction):
        try: await interaction.response.defer()
        except: return
        plan_id = f"VP-{int(datetime.now(timezone.utc).timestamp())}"; created = str(datetime.now(timezone.utc))
        row = [plan_id, self.wing_name, self.plan_type, self.vision_statement.value, self.targets.value, interaction.user.name, created, "Active"]
        if await apps_post("VisionPlans", row, guild=interaction.guild):
            embed = discord.Embed(title=f"🌟 {self.plan_type} Vision Plan: {self.wing_name}", description=f"**Vision:**\n{self.vision_statement.value}", color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
            embed.add_field(name="Targets", value=self.targets.value, inline=False)
            sc = await apps_get("WingShowcase", guild=interaction.guild)
            tc = interaction.channel
            if sc and len(sc) > 1:
                for r in sc[1:]:
                    if r[0] == self.wing_name and len(r) > 1 and r[1]:
                        try:
                            tc = interaction.guild.get_channel(int(r[1])) or await bot.fetch_channel(int(r[1]))
                            if tc: break
                        except: continue
            await tc.send(content=f"📢 New {self.plan_type} Vision Plan!", embed=embed)
            await interaction.followup.send("✅ Vision Plan saved!", ephemeral=True)
            await send_log(interaction.guild, f"🌟 {self.plan_type} Vision Plan set for **{self.wing_name}**")
            asyncio.create_task(update_wing_showcase(interaction.guild, self.wing_name))
