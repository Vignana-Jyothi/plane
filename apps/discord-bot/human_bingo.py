import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio

# File to store bingo state
DATA_FILE = "bingo_data.json"

BINGO_TRAITS = [
    "Has a pet dog", "Speaks 3+ languages", "Is left-handed", "Plays an instrument",
    "Has a tattoo", "Born same month as you", "Been to 5+ countries", "Likes pineapple on pizza",
    "Has broken a bone", "Can code in C++", "Has met a celeb", "Drinks black coffee",
    "Has a cat", "Read 5+ books this year", "Knows martial arts", "Has siblings",
    "Can juggle", "Never played Minecraft", "Loves spicy food", "Has 0 unread emails",
    "Wears glasses", "Has dyed their hair", "Can whistle loudly", "Been on a motorcycle",
    "Fav color is green", "Plays chess", "Has a garden", "Has run 5k+", "Allergic to nuts",
    "Knows how to surf", "Never broke a bone", "Has a twin", "Can do a backflip"
]

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Error loading bingo data: {e}. Resetting to empty.")
        # Backup corrupted file
        if os.path.exists(DATA_FILE):
            try: os.rename(DATA_FILE, f"{DATA_FILE}.bak")
            except: pass
        return {}

def save_data(data):
    try:
        # Write to a temporary file first to prevent corruption during crash
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(temp_file, DATA_FILE)
    except Exception as e:
        print(f"❌ Error saving bingo data: {e}")

def check_bingo(marked):
    # marked is a dict mapping index (0-24) to marked status (bool)
    # Rows
    for i in range(5):
        if all(marked.get(str(i * 5 + j)) for j in range(5)):
            return True
    # Cols
    for j in range(5):
        if all(marked.get(str(i * 5 + j)) for i in range(5)):
            return True
    # Diagonals
    if all(marked.get(str(i * 5 + i)) for i in range(5)):
        return True
    if all(marked.get(str(i * 5 + (4 - i))) for i in range(5)):
        return True
    return False

class BingoButton(discord.ui.Button):
    def __init__(self, index: int, trait: str, is_marked: bool, marked_user: str = None, user_id: str = ""):
        self.index = index
        self.trait = trait
        self.user_id = user_id
        
        label = trait
        if len(label) > 80:
            label = label[:77] + "..."
            
        style = discord.ButtonStyle.success if is_marked else discord.ButtonStyle.secondary
        if is_marked and marked_user:
            label = f"✓ {marked_user}"
            
        super().__init__(style=style, label=label, row=index // 5, custom_id=f"bingo_btn_{user_id}_{index}")
        self.disabled = is_marked

    async def callback(self, interaction: discord.Interaction):
        # We must respond immediately to prevent "Interaction Failed"
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=False)
        except (discord.errors.NotFound, discord.errors.InteractionResponded):
            return
        except Exception as e:
            print(f"⚠️ Error deferring interaction: {e}")
            return
            
        try:
            await interaction.followup.send(f"📍 **{self.trait}**\n*Please type and `@mention` the person who fits this trait in this thread.*", ephemeral=False)
            
            data = load_data()
            user_id = str(interaction.user.id)
            if user_id not in data:
                return
                
            data[user_id]['waiting_for'] = self.index
            save_data(data)
        except Exception as e:
            print(f"❌ Error in BingoButton callback: {e}")

class BingoView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=None)
        data = load_data()
        user_data = data.get(user_id)
        if not user_data:
            return
            
        board = user_data['board']
        marked = user_data['marked']
        marked_users = user_data.get('marked_users', {})
        
        for i, trait in enumerate(board):
            is_marked = marked.get(str(i), False)
            marked_user = marked_users.get(str(i))
            self.add_item(BingoButton(i, trait, is_marked, marked_user, user_id))

class BingoStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create My Bingo Board", style=discord.ButtonStyle.primary, custom_id="start_bingo_btn")
    async def start_bingo(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Prevent double acknowledgment
        if interaction.response.is_done():
            return

        # Check if they already have one before deferring to save time
        data = load_data()
        user_id = str(interaction.user.id)
        
        if user_id in data and 'thread_id' in data[user_id]:
            try:
                thread = interaction.channel.guild.get_thread(data[user_id]['thread_id'])
                if thread:
                    return await interaction.response.send_message(f"You already have a Bingo game running here: {thread.mention}", ephemeral=True)
            except:
                pass

        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.InteractionResponded:
            return
        except discord.errors.NotFound:
            return

        try:
            channel = interaction.channel
            
            # Check permissions
            permissions = channel.permissions_for(interaction.guild.me)
            if not permissions.create_private_threads or not permissions.send_messages_in_threads:
                return await interaction.followup.send("❌ The bot is missing permissions to create **Private Threads** or send messages in them. Please check server settings!", ephemeral=True)

            # Create a private thread natively
            thread = await channel.create_thread(
                name=f"Bingo - {interaction.user.name}",
                type=discord.ChannelType.private_thread,
                invitable=False
            )
            await thread.add_user(interaction.user)
            
            # Generate board
            board = random.sample(BINGO_TRAITS, 25)
            
            # Init marked dict
            marked = {str(i): False for i in range(25)}
            
            data[user_id] = {
                "board": board,
                "marked": marked,
                "marked_users": {},
                "thread_id": thread.id,
                "waiting_for": -1
            }
            save_data(data)
            
            embed = discord.Embed(
                title=f"🎲 {interaction.user.name}'s Human Bingo",
                description="Find people in the server who match the traits below!\n\n1. Click a trait button.\n2. `@mention` the person who fits it in this thread.\n3. Get 5 in a row to win!",
                color=discord.Color.green()
            )
            
            view = BingoView(user_id)
            msg = await thread.send(content=f"{interaction.user.mention}", embed=embed, view=view)
            
            data[user_id]["message_id"] = msg.id
            save_data(data)
            
            await interaction.followup.send(f"✅ Your Bingo board has been created: {thread.mention}", ephemeral=True)
            
        except discord.errors.Forbidden:
             await interaction.followup.send("❌ Error: I don't have permission to create threads in this channel. (Forbidden)", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error while creating your Bingo board: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    # Register dynamic views for persistence loop
    try:
        data = load_data()
        count = 0
        for uid in list(data.keys()):
            # Only register views for users who have a valid game record
            # We don't want to instantiate too many views if not needed
            if 'board' in data[uid] and 'thread_id' in data[uid]:
                try:
                    bot.add_view(BingoView(uid))
                    count += 1
                except Exception as ve:
                    print(f"⚠️ Could not register view for {uid}: {ve}")
        if count > 0:
            print(f"✅ Re-injected {count} Bingo views.")
    except Exception as e:
        print(f"❌ Critical error in Bingo setup loop: {e}")
    # Add slash commands
    @bot.tree.command(name="setupbingo", description="Initialize the Human Bingo game channel")
    @app_commands.describe(channel="The channel for the Human Bingo lobby")
    async def setup_bingo(interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ This command requires administrator permissions.", ephemeral=True)
            
        embed = discord.Embed(
            title="🎯 Welcome to Human Bingo!",
            description="Get to know your team! Click the button below to generate your own private Bingo Board.\n\n*Your board will be generated in a private thread where you can play without influencing others.*",
            color=discord.Color.blue()
        )
        
        await channel.send(embed=embed, view=BingoStartView())
        await interaction.response.send_message(f"✅ Bingo lobby initialized in {channel.mention}!", ephemeral=True)

    @bot.tree.command(name="endbingo", description="End the Bingo game and show Leaderboard (Wing Master)")
    async def end_bingo(interaction: discord.Interaction):
        # Check for Wing Master or Admin
        is_admin = interaction.user.guild_permissions.administrator
        has_wing_master_role = any(role.id == 1468504967844462692 for role in interaction.user.roles)
        if not (is_admin or has_wing_master_role):
            return await interaction.response.send_message("❌ This command requires Wing Master permissions.", ephemeral=True)
            
        data = load_data()
        if not data:
            return await interaction.response.send_message("❌ No Bingo game is currently running.", ephemeral=True)
            
        await interaction.response.defer(ephemeral=False)
        
        # Calculate leaderboard
        leaderboard = []
        for user_id, user_data in data.items():
            marked_count = sum(1 for v in user_data.get('marked', {}).values() if v)
            
            try:
                member = interaction.guild.get_member(int(user_id))
                name = member.display_name if member else f"User {user_id}"
            except:
                name = f"User {user_id}"
                
            leaderboard.append((name, marked_count))
            
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="🏆 Human Bingo Leaderboard 🏆",
            description="The Bingo game has concluded! Here are the members with the most traits checked:",
            color=discord.Color.gold()
        )
        
        for i, (name, score) in enumerate(leaderboard[:15]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
            embed.add_field(name=f"{medal} #{i+1} {name}", value=f"{score} Traits Found", inline=False)
            
        if not leaderboard:
            embed.description = "The Bingo game has ended, but nobody found any traits!"
            
        # Optional: Reset data so a new game can start
        save_data({})
        
        await interaction.followup.send(content="**The Bingo Game has officially ended!**", embed=embed)

    # Re-register views
    bot.add_view(BingoStartView())
    
    # Message listener to catch mentions and update board
    @bot.listen('on_message')
    async def on_bingo_message(message: discord.Message):
        try:
            if message.author.bot:
                return
                
            # Is it in a private thread?
            if message.channel.type != discord.ChannelType.private_thread:
                return
                
            data = load_data()
            user_id = str(message.author.id)
            
            if user_id not in data:
                return
                
            user_data = data[user_id]
            if user_data.get('thread_id') != message.channel.id:
                return
            
            waiting_index = user_data.get('waiting_for', -1)
            if waiting_index == -1:
                return
                
            if not message.mentions:
                await message.channel.send("❌ You need to `@mention` a user to mark off this trait! Try again.", delete_after=5)
                return
                
            # Optional: restrict mentioning oneself
            mentioned_user = message.mentions[0]
            if mentioned_user.id == message.author.id:
                await message.channel.send("❌ You cannot mention yourself for Bingo!", delete_after=5)
                return
                
            if mentioned_user.bot:
                await message.channel.send("❌ You cannot mention a bot for Bingo!", delete_after=5)
                return
                
            # Check if user was already used
            used_users = list(user_data.get('marked_users', {}).values())
            if mentioned_user.name in used_users:
                await message.channel.send(f"❌ You have already used **{mentioned_user.name}** for another trait. Find someone else!", delete_after=5)
                return

            # Mark it!
            idx_str = str(waiting_index)
            user_data['marked'][idx_str] = True
            
            if 'marked_users' not in user_data:
                user_data['marked_users'] = {}
                
            user_data['marked_users'][idx_str] = mentioned_user.name
            user_data['waiting_for'] = -1
            
            save_data(data)
            
            # React to confirm
            await message.add_reaction("✅")
            
            # Re-render UI
            try:
                msg_id = user_data.get("message_id")
                if msg_id:
                    msg = await message.channel.fetch_message(msg_id)
                    view = BingoView(user_id)
                    await msg.edit(view=view)
            except Exception as e:
                print(f"Error updating Bingo view: {e}")
                
            # Check win
            if check_bingo(user_data['marked']) and not user_data.get('won', False):
                user_data['won'] = True
                save_data(data)
                await message.channel.send(f"🎉 **BINGO!** Congratulations {message.author.mention}, you matched 5 in a row! 🎉\n*(Keep playing! The ultimate winner is whoever gets the most overall checks by the end!)*")
        except Exception as e:
            print(f"❌ Critical error in on_bingo_message: {e}")
