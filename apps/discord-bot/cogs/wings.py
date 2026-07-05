import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from utils import apps_post, is_wing_master, send_log
from logic.wings import update_wing_showcase
from ui.components import VisionPlanModal, RoleSelectionView

class WingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setupwing", description="Initialize wing showcase channel (Admin only)")
    async def setup_wing(self, interaction: discord.Interaction, wing: discord.Role, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        await interaction.response.defer()
        row = [wing.name, str(channel.id), "", "", str(datetime.now(timezone.utc)), 0, 0, 0]
        if await apps_post("WingShowcase", row, guild=interaction.guild):
            await update_wing_showcase(interaction.guild, wing.name)
            await interaction.followup.send(f"✅ Setup complete for **{wing.name}** in {channel.mention}!")

    @app_commands.command(name="setvisionplan", description="Set a weekly or monthly vision plan for a wing")
    @app_commands.choices(plan_type=[app_commands.Choice(name="Weekly", value="Weekly"), app_commands.Choice(name="Monthly", value="Monthly")])
    async def set_vision_plan(self, interaction: discord.Interaction, plan_type: str, wing: discord.Role):
        if not is_wing_master(interaction.user, wing.name):
            return await interaction.response.send_message(f"❌ Restricted to Wing Masters or {wing.name} Leads.", ephemeral=True)
        await interaction.response.send_modal(VisionPlanModal(wing.name, plan_type))

    @app_commands.command(name="setuproles", description="Initialize a self-assign roles channel (Admin)")
    async def setup_roles(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        options = []
        skip = ["vision", "member", "shadow member", "wing master", "app", "startup manager"]
        for role in interaction.guild.roles:
            if role.name == "@everyone" or role.managed or role.permissions.administrator: continue
            if role.name.lower() in skip or role.is_bot_managed(): continue
            options.append(discord.SelectOption(label=role.name, value=str(role.id)))
            if len(options) >= 25: break
        from config import MEMBER_ROLE_ID, SHADOW_MEMBER_ROLE_ID
        view = RoleSelectionView(options, MEMBER_ROLE_ID, SHADOW_MEMBER_ROLE_ID)
        embed = discord.Embed(title="🎭 Role Selection", description="Select your Member Type and Wing below.", color=discord.Color.purple())
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Dynamic roles menu initialized!", ephemeral=True)

    @app_commands.command(name="setupreminder", description="Set a specific reminder channel for a wing role (Admin only)")
    async def setup_reminder(self, interaction: discord.Interaction, wing: discord.Role, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only.", ephemeral=True)
        await interaction.response.defer()
        if await apps_post("ReminderChannelsUpdate", {"wing_name": wing.name, "channel_id": str(channel.id)}, guild=interaction.guild):
            await interaction.followup.send(f"✅ Reminders for **{wing.name}** will now be sent to {channel.mention}!")

async def setup(bot):
    await bot.add_cog(WingsCog(bot))
