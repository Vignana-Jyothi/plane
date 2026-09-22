import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from utils import apps_get, apps_post, is_wing_master, send_log
from ui.components import MeetingModal

class MeetingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="schedulemeeting", description="Schedule a meeting")
    async def schedule_meeting(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.send_modal(MeetingModal(role))

    @app_commands.command(name="deletemeeting", description="Delete a scheduled meeting")
    async def delete_meeting(self, interaction: discord.Interaction, meeting_id: str):
        await interaction.response.defer(ephemeral=True)
        meetings = await apps_get("Meetings", guild=interaction.guild)
        meeting = next((m for m in meetings[1:] if str(m[0]) == str(meeting_id)), None)
        if not meeting: return await interaction.followup.send("❌ Meeting not found.", ephemeral=True)
        if interaction.user.name != meeting[6] and not is_wing_master(interaction.user):
            return await interaction.followup.send("❌ Unauthorized.", ephemeral=True)
        if await apps_post("MeetingsUpdate", {"meeting_id": meeting_id, "status": "Deleted"}, guild=interaction.guild):
            await interaction.followup.send(f"✅ Meeting `{meeting_id}` deleted.", ephemeral=True)

    @app_commands.command(name="meetings", description="View scheduled meetings")
    async def view_meetings(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await apps_get("Meetings", guild=interaction.guild)
        if not data or len(data) < 2: return await interaction.followup.send("No meetings found.")
        embed = discord.Embed(title="📅 Scheduled Meetings", color=discord.Color.blue())
        for m in data[1:]:
            if len(m) > 11 and str(m[11]).lower() == "scheduled":
                embed.add_field(name=f"{m[2]} (ID: {m[0]})", value=f"**Wing:** {m[1]}\n**Time:** {m[4]}\n**Details:** {m[3]}", inline=False)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MeetingsCog(bot))
