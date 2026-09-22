import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from utils import apps_post, is_wing_master
from logic.permissions import ensure_category_restrictions

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addmember", description="Add a member to the Members sheet (Wing Masters)")
    async def add_member(self, interaction: discord.Interaction, person: discord.Member, role: str):
        if not is_wing_master(interaction.user): return await interaction.response.send_message("❌ Restricted.", ephemeral=True)
        await interaction.response.defer()
        if await apps_post("Members", [person.name, role, "Active"], guild=interaction.guild):
            await interaction.followup.send(f"✅ Added {person.mention}!")

    @app_commands.command(name="processdelays", description="Process overdue tasks (Wing Masters)")
    async def process_delays(self, interaction: discord.Interaction):
        if not is_wing_master(interaction.user): return await interaction.response.send_message("❌ Restricted.", ephemeral=True)
        await interaction.response.defer()
        if await apps_post("ProcessDelaysAndScores", {"action": "run"}, guild=interaction.guild):
            await interaction.followup.send("✅ Successfully processed delays!")

    @app_commands.command(name="sync", description="Sync all slash commands (Admin only)")
    async def sync(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(f"✅ Successfully synced {len(synced)} commands.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: {e}", ephemeral=True)

    @app_commands.command(name="syncperms", description="Sync Member & Shadow Member category permissions (Admins)")
    async def sync_perms(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await ensure_category_restrictions(interaction.guild)
        await interaction.followup.send("✅ Permissions synced.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
