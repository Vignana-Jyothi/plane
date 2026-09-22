import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from help_ui import HelpView, get_command_help

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Interactive guide to all bot commands")
    @app_commands.describe(command="Specific command to get details for")
    async def help_cmd(self, interaction: discord.Interaction, command: Optional[str] = None):
        if command:
            embed = get_command_help(command)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="✨ VJ Startups - Command Hub",
            description=(
                "Welcome! This bot manages tasks, targets, meetings, and performance scores.\n\n"
                "**How to use:**\n"
                "• Use the **dropdown menu** below to browse by category.\n"
                "• Click **Quick Overview** to see core features.\n"
                "• Type `/` to see all available slash commands."
            ),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Empowering VJ Startups • Built for productivity")
        await interaction.response.send_message(embed=embed, view=HelpView())

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
