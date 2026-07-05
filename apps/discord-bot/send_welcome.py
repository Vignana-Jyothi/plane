import os
import discord
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1465934184865468561

class WelcomeBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            try:
                channel = await self.fetch_channel(CHANNEL_ID)
            except Exception as e:
                print(f"Could not fetch channel: {e}")
                await self.close()
                return

        embed = discord.Embed(
            title="🚀 Welcome to VJ Startups!",
            description=(
                "We're thrilled to have you here! VJ Startups is a community dedicated to building, "
                "collaborating, and pushing the boundaries of what's possible.\n\n"
                "Here is everything you need to know to get started."
            ),
            color=0x2b2d31 # Sleek dark color
        )
        
        embed.add_field(
            name="🎭 1. Grab Your Roles",
            value=(
                "Choose your roles to access the right channels and teams:\n"
                "• Join as a **Member** or **Shadow Member** depending on your availability.\n"
                "• Select your **Wing/Team** to collaborate on focused projects alongside others."
            ),
            inline=False
        )

        embed.add_field(
            name="🤖 2. Productivity Tools",
            value=(
                "We use our custom bot to manage tasks and stay productive:\n"
                "• Type `/createtask` anywhere to create tasks with progress metrics and deadlines.\n"
                "• Type `/creategoal` to establish weekly or monthly targets for your wing.\n"
                "• Use the interactive buttons on task messages to log updates and stay accountable."
            ),
            inline=False
        )
        
        embed.add_field(
            name="🧭 3. Quick Navigation",
            value=(
                f"• <#{CHANNEL_ID}> - This channel (Welcome & Rules)\n"
                "• **#announcements** - Important updates and events.\n"
                "• **#general** - Casual chat and introductions.\n"
                "• **#showcase** - View weekly progress and achievements from all wings.\n"
                "*(Note: You can update the channel names/IDs to make them clickable later)*"
            ),
            inline=False
        )

        embed.add_field(
            name="📜 Server Rules",
            value=(
                "• **Be Respectful**: Keep conversations professional, kind, and supportive.\n"
                "• **No Spam**: Limit self-promotion to designated channels.\n"
                "• **Stay on Topic**: Help us keep the server organized by using the correct channels."
            ),
            inline=False
        )
        
        embed.set_footer(text="Let's build something amazing together! 💡")

        try:
            msg = await channel.send(embed=embed)
            print(f"Successfully sent the updated welcome embed! Message ID: {msg.id}")
        except Exception as e:
            print(f"Failed to send message: {e}")
            
        await self.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN is not set in the .env file.")
    else:
        print("Starting bot to send welcome message...")
        client = WelcomeBot()
        client.run(TOKEN)
