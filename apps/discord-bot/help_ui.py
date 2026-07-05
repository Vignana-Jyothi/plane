import discord
from typing import Optional, List

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Task Management", description="Create and manage tasks/goals", emoji="🎯", value="tasks"),
            discord.SelectOption(label="Meetings", description="Schedule and view team meetings", emoji="📅", value="meetings"),
            discord.SelectOption(label="Management & Wings", description="Wing Master and Admin tools", emoji="🛠️", value="management"),
            discord.SelectOption(label="Tracking & Analytics", description="Scores and dashboards", emoji="📊", value="analytics"),
            discord.SelectOption(label="Games", description="Human Bingo and more", emoji="🎲", value="games"),
        ]
        super().__init__(placeholder="Choose a category to explore...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        embed = discord.Embed(color=discord.Color.blue())
        
        if value == "tasks":
            embed.title = "🎯 Task Management Commands"
            embed.description = (
                "**/createtask** - Create a new task with progress metrics.\n"
                "**/mytasks** - View your own active tasks.\n"
                "**/viewtasks** - View tasks assigned to another member.\n"
                "**/updateprogress** - Update status/metrics for a task.\n"
                "**/delegate** - Reassign a task to someone else.\n"
                "**/board** - View the Kanban board for a wing.\n"
                "**/creategoal** - Create a Weekly or Monthly target goal.\n"
                "**/addweeklytarget** - Shortcut to add a weekly wing target.\n"
                "**/addmonthlytarget** - Shortcut to add a monthly wing target.\n"
                "**/createplan** - Create a long-term strategic plan.\n"
                "**/deletetask** - Delete a task or target (Creator/Admin only)."
            )
            
        elif value == "meetings":
            embed.title = "📅 Meeting Commands"
            embed.description = (
                "**/schedulemeeting** - Schedule a meeting for a specific role.\n"
                "**/meetings** - Show all upcoming scheduled meetings.\n"
                "**/deletemeeting** - Cancel a meeting (Creator/Admin only)."
            )

        elif value == "management":
            embed.title = "🛠️ Management & Wing Commands"
            embed.description = (
                "**/setvisionplan** - Define weekly/monthly strategy for a wing.\n"
                "**/setupwing** - Initialize a showcase channel for wing progress.\n"
                "**/setupreminder** - Redirect wing reminders to a specific channel.\n"
                "**/setuproles** - Create self-assign member selection menu.\n"
                "**/addmember** - Register a member manually in tracking.\n"
                "**/processdelays** - Manually trigger score recalculations.\n"
                "**/sync** - Synchronize slash commands with Discord (Admin).\n"
                "**/syncperms** - Sync Shadow Member category restrictions."
            )

        elif value == "analytics":
            embed.title = "📊 Tracking & Analytics"
            embed.description = (
                "**/myscore** - View your performance metrics and score rank.\n"
                "**/viewscores** - View global and local wing leaderboards.\n"
                "**/wingdashboard** - Detailed analytics for a specific wing.\n"
                "**/viewtargets** - List active high-level targets for a wing.\n"
                "**/targettasks** - List all tasks linked to a specific target."
            )

        elif value == "games":
            embed.title = "🎲 Game Commands"
            embed.description = (
                "**/setupbingo** - Initialize Human Bingo lobby.\n"
                "**/endbingo** - End bingo game and show leaderboard."
            )

        embed.set_footer(text="Pro Tip: Use /help [command] for direct details.")
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown())

    @discord.ui.button(label="Quick Overview", style=discord.ButtonStyle.secondary, row=1)
    async def overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 VJ Startups Bot - Command Hub",
            description=(
                "Welcome to the startup management center! Use the menu below to explore categories.\n\n"
                "**Core Systems:**\n"
                "• 💠 **Tasks:** Create and track work with metrics.\n"
                "• 💠 **Targets:** Set weekly and monthly wing goals.\n"
                "• 💠 **Meetings:** Integrated scheduling and tracking.\n"
                "• 💠 **Scores:** Performance-based gamification."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="React to task messages with ✅ to complete them!")
        await interaction.response.edit_message(embed=embed, view=self)

def get_command_help(command_name: str) -> discord.Embed:
    cmd = command_name.lower().strip().replace("/", "")
    embed = discord.Embed(color=discord.Color.from_rgb(88, 101, 242))
    
    if cmd == "createtask":
        embed.title = "🎯 Command: /createtask"
        embed.description = "Creates a new task with custom metrics (Percentage/Count) and assigns it to a member within a wing."
        embed.set_footer(text="Permission: Anyone")
    elif cmd == "setvisionplan":
        embed.title = "🌟 Command: /setvisionplan"
        embed.description = "Sets a Weekly or Monthly strategy for a wing. Pulls from the VisionPlans sheet and updates channel dashboards."
        embed.set_footer(text="Permission: Wing Master / Lead")
    elif cmd == "processdelays":
        embed.title = "⏰ Command: /processdelays"
        embed.description = "Syncs overdue tasks and recalculates scores. Points: H(15), M(10), L(5). Prevents bot assignments automatically."
        embed.set_footer(text="Permission: Wing Master / Admin")
    else:
        embed.title = f"🔍 Command: /{cmd}"
        embed.description = f"Detailed help for `{cmd}` is available in the interactive dropdown menu."
        
    return embed
