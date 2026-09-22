import os
import discord
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1465939722529673317

class RulesBot(discord.Client):
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
            title="📜 VJ Startups - Server Governance & Rules",
            description=(
                "Welcome to the official **VJ Startups** rulebook.\n"
                "To maintain a high-quality, productive environment for all entrepreneurs and builders, "
                "we enforce a set of distinct community standards. Please review them carefully."
            ),
            color=0xda373c # A bold red to signify rules
        )
        
        embed.add_field(
            name="🤝 1. Code of Conduct",
            value=(
                "**1.1. Be Professional:** Treat everyone with respect. Harassment, discrimination, hate speech, "
                "or personal attacks will result in immediate action.\n"
                "**1.2. Constructive Feedback Only:** We encourage peer review, but keep your criticism constructive and helpful.\n"
                "**1.3. Inclusivity:** We welcome builders from all backgrounds and experience levels. Foster an environment of learning."
            ),
            inline=False
        )

        embed.add_field(
            name="🚫 2. Anti-Spam & Promotion Policy",
            value=(
                "**2.1. No Unsolicited DMs:** Do not mass-message server members without their explicit consent.\n"
                "**2.2. Dedicated Promotion:** Self-promotion, project links, and recruitment belong *only* in the designated promotional channels. "
                "Posting them elsewhere will lead to removal.\n"
                "**2.3. Meaningful Engagement:** Do not bump threads or spam channels with low-effort messages (e.g., 'gm', 'hi') simply to farm activity."
            ),
            inline=False
        )

        embed.add_field(
            name="💼 3. Collaboration & Productivity",
            value=(
                "**3.1. Accountability:** If you take on a task in a wing or team, communicate proactively if you are blocked or missing a deadline.\n"
                "**3.2. Bot Usage:** Utilize the productivity bot efficiently (e.g., `/createtask`). Do not spam the bot commands or misuse them in off-topic channels.\n"
                "**3.3. IP Respect:** Do not steal, plagarize, or claim ownership of ideas and projects shared by others in this community."
            ),
            inline=False
        )

        embed.add_field(
            name="🚨 4. Enforcement & Moderation",
            value=(
                "• **Strikes:** Violations of these rules may result in a formal warning or strike.\n"
                "• **Timeouts/Bans:** Repeated offenses or severe violations (e.g., malicious links, severe harassment) will result in an instant ban.\n"
                "• **Reporting:** If you spot rule-breaking behavior, please ping a Moderator or Wing Master rather than escalating the situation yourself."
            ),
            inline=False
        )
        
        embed.set_footer(text="By participating in this server, you agree to abide by these rules. Let's build!")

        try:
            msg = await channel.send(embed=embed)
            print(f"Successfully sent the extensive rules embed! Message ID: {msg.id}")
        except Exception as e:
            print(f"Failed to send message: {e}")
            
        await self.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN is not set in the .env file.")
    else:
        print("Starting bot to send extensive rules...")
        client = RulesBot()
        client.run(TOKEN)
