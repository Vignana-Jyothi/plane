import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from utils import apps_get, is_wing_master, calculate_wing_metrics

class AnalyticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="myscore", description="View your task score and statistics")
    async def my_score(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await apps_get("ScoreBoards", guild=interaction.guild)
        username = interaction.user.name
        score_data = None
        if data and len(data) > 1:
            score_data = next((row for row in data[1:] if len(row) > 6 and row[0] == username), None)
            
        if not score_data:
            score_data = [username, 0, 0, "0%", 0, 0, "New/Not Started"]
            
        remarks = str(score_data[6])
        color = discord.Color.blue()
        if "Green" in remarks: color = discord.Color.green()
        elif "Orange" in remarks: color = discord.Color.orange()
        elif "Red" in remarks: color = discord.Color.red()
        
        embed = discord.Embed(title=f"📊 Performance Stats: {username}", description=f"**Status:** {remarks}", color=color)
        embed.add_field(name="🎯 Total Assigned", value=f"`{score_data[1]}`", inline=True)
        embed.add_field(name="✅ Completed", value=f"`{score_data[2]}`", inline=True)
        embed.add_field(name="🚀 Pace", value=f"`{score_data[3]}`", inline=True)
        embed.add_field(name="⏰ Overdue Days", value=f"`{score_data[4]}`", inline=True)
        embed.add_field(name="🏆 Overall Score", value=f"**{score_data[5]}**", inline=True)
        embed.add_field(name="📈 Rating", value=remarks.split()[-1] if " " in remarks else remarks, inline=True)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Keep up the great work! Scores update regularly.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="viewscores", description="View members' scoreboards")
    async def view_scores(self, interaction: discord.Interaction, wing: Optional[discord.Role] = None):
        await interaction.response.defer()
        scores_data = await apps_get("ScoreBoards", wing=wing.name if wing else None, guild=interaction.guild)
        members_data = await apps_get("Members", guild=interaction.guild)
        
        member_roles = {r[0]: r[1] for r in members_data[1:] if r and len(r) > 1}
        member_scores = {}
        for row in scores_data[1:]:
            if len(row) > 6 and row[0]:
                member_scores[row[0]] = {
                    "name": row[0], "assigned": row[1], "done": row[2],
                    "score": float(row[5]) if row[5] else 0.0, "remarks": row[6],
                    "wing": member_roles.get(row[0], "Unknown")
                }
        
        for name, role in member_roles.items():
            if name not in member_scores:
                member_scores[name] = {"name": name, "assigned": 0, "done": 0, "score": 0.0, "remarks": "⚪ New", "wing": role}
        
        sorted_members = sorted(member_scores.values(), key=lambda x: x["score"], reverse=True)
        
        title_text = f"🏆 Scoreboard: {wing.name}" if wing else "🏆 Overall Scoreboards"
        embed = discord.Embed(title=title_text, color=discord.Color.gold())
        
        limit = 10 if not wing else 20
        desc = f"**🌟 Top Performers**\n"
        for i, m in enumerate(sorted_members[:limit], 1):
            emoji = "🟢" if "Green" in m['remarks'] else "🟠" if "Orange" in m['remarks'] else "🔴" if "Red" in m['remarks'] else "⚪"
            desc += f"{i}. {emoji} **{m['name']}** - **{m['score']}** | {m['done']}/{m['assigned']}\n"
        embed.description = desc
        
        if not wing:
            wings = sorted(list(set(m['wing'] for m in sorted_members if m['wing'] != "Unknown")))
            for w in wings:
                wing_members = [m for m in sorted_members if m['wing'] == w][:5]
                if wing_members:
                    wing_desc = "\n".join([f"{i}. **{m['name']}** - **{m['score']}**" for i, m in enumerate(wing_members, 1)])
                    embed.add_field(name=f"Top 5 {w}", value=wing_desc, inline=True)
                
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="wingdashboard", description="View detailed wing analytics")
    async def wing_dashboard(self, interaction: discord.Interaction, wing: discord.Role):
        await interaction.response.defer()
        data = await apps_get("Tasks", wing=wing.name)
        tasks = [t for t in data[1:] if len(t) > 7 and t[7] == wing.name and t[3] != "Deleted"]
        metrics = calculate_wing_metrics(tasks)
        
        weekly = [t for t in tasks if len(t) > 12 and t[12] == "Weekly"]
        monthly = [t for t in tasks if len(t) > 12 and t[12] == "Monthly"]
        
        def progress_str(tlist):
            if not tlist: return "None set"
            done = len([t for t in tlist if t[3] == "Done"])
            return f"**{done}/{len(tlist)} achieved** ({int(done/len(tlist)*100) if tlist else 0}%)"

        embed = discord.Embed(title=f"📊 {wing.name} Wing Dashboard", description="Comprehensive productivity overview", color=discord.Color.gold())
        embed.add_field(name="🎯 Target Progress", value=f"📅 **Weekly:** {progress_str(weekly)}\n🗓️ **Monthly:** {progress_str(monthly)}", inline=False)
        embed.add_field(name="📈 Overall Statistics", value=f"**Total Items:** {metrics['total']}\n**Completed:** {metrics['done']} ({metrics['completion_rate']}%)\n**In Progress:** {metrics['in_progress']}", inline=False)
        
        members = set()
        for t in tasks:
            if len(t) > 6 and t[6] != "Unassigned": members.add(t[6])
        if members: embed.add_field(name="👥 Active Members", value=", ".join(list(members)[:10]), inline=False)
        
        # Add Scoreboard highlight for the wing
        scores_data = await apps_get("ScoreBoards", wing=wing.name, guild=interaction.guild)
        if scores_data and len(scores_data) > 1:
            top_member = sorted(scores_data[1:], key=lambda x: float(x[5]) if len(x)>5 else 0, reverse=True)[0]
            embed.add_field(name="🏆 Wing MVP", value=f"**{top_member[0]}** with score **{top_member[5]}**", inline=True)
            
        # Add Delay summary
        delay_data = await apps_get("DelayTracker", wing=wing.name, guild=interaction.guild)
        if delay_data and len(delay_data) > 1:
            total_delays = sum(int(row[3]) for row in delay_data[1:] if len(row) > 3)
            embed.add_field(name="⏰ Delay Status", value=f"Total overdue tasks: **{len(delay_data)-1}**\nTotal delay days: **{total_delays}**", inline=True)
        
        embed.set_footer(text=f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="viewtargets", description="View active weekly and monthly targets for a wing")
    async def view_targets(self, interaction: discord.Interaction, wing: discord.Role):
        await interaction.response.defer()
        data = await apps_get("Tasks")
        if not data or len(data) < 2: return await interaction.followup.send("No targets found.")
        targets = [t for t in data[1:] if len(t) > 12 and t[12] in ["Weekly", "Monthly"] and t[7] == wing.name and t[3] != "Deleted"]
        if not targets: return await interaction.followup.send(f"No active targets for {wing.name}.")
        embed = discord.Embed(title=f"🎯 Active Goals - {wing.name}", color=discord.Color.blue())
        for t in targets:
            sub = [st for st in data[1:] if len(st) > 22 and str(st[22]) == str(t[0]) and st[3] != "Deleted"]
            done = [st for st in sub if st[3] == "Done"]
            embed.add_field(name=f"🏁 {t[1]}", value=f"**{t[12]}** | {t[3]}\n✅ **{len(done)}/{len(sub)}** tasks\nID: `{t[0]}`", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="targettasks", description="View all tasks for a specific target")
    async def target_tasks(self, interaction: discord.Interaction, target_id: str):
        await interaction.response.defer()
        data = await apps_get("Tasks")
        target = next((t for t in data[1:] if str(t[0]) == target_id), None)
        if not target: return await interaction.followup.send("Target not found.")
        sub = [st for st in data[1:] if len(st) > 22 and str(st[22]) == target_id and st[3] != "Deleted"]
        embed = discord.Embed(title=f"📋 Tasks for: {target[1]}", description=f"ID: `{target_id}` | Status: {target[3]}", color=discord.Color.green())
        for st in sub:
            embed.add_field(name=f"{'✅' if st[3]=='Done' else '⏳'} {st[1]}", value=f"ID: `{st[0]}` | @{st[6]}", inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="delaytracker", description="View the delay tracker for a wing")
    async def delay_tracker(self, interaction: discord.Interaction, wing: discord.Role):
        await interaction.response.defer()
        delay_data = await apps_get("DelayTracker", wing=wing.name, guild=interaction.guild)
        if not delay_data or len(delay_data) < 2:
            return await interaction.followup.send(f"✅ No delays tracked for **{wing.name}**.")
            
        embed = discord.Embed(title=f"⏰ Delay Tracker: {wing.name}", color=discord.Color.red())
        tasks_data = await apps_get("Tasks", wing=wing.name, guild=interaction.guild)
        
        description = ""
        for row in delay_data[1:15]: # Show top 15 delays
            tid = row[0]; name = row[1]; days = row[3]
            task_title = "Unknown Task"
            if tasks_data:
                task = next((t for t in tasks_data[1:] if str(t[0]) == str(tid)), None)
                if task: task_title = task[1]
            
            description += f"• `{tid}` **{task_title}** - @{name} (**{days} days**)\n"
        
        if not description: description = "No active delays."
        embed.description = description
        embed.set_footer(text=f"Showing top delays for {wing.name}")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AnalyticsCog(bot))
