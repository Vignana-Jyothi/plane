import discord
import asyncio
from datetime import datetime, timezone, timedelta
from utils import apps_get, apps_post, calculate_wing_metrics, create_progress_bar, send_log
from bot_base import bot

async def update_wing_showcase(guild, wing_name):
    """Update the wing showcase channel with latest data"""
    try:
        # Get wing showcase channel info
        showcase_data = await apps_get("WingShowcase", guild=guild)
        if not showcase_data or len(showcase_data) < 2:
            return
        
        # Find the wing's showcase info
        wing_showcase = None
        for row in showcase_data[1:]:
            if row[0] == wing_name:
                wing_showcase = row
                break
        
        if not wing_showcase or not wing_showcase[1]:  # No channel_id
            return
        
        channel_id = int(wing_showcase[1])
        channel = guild.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        
        if not channel:
            return
        
        # Get all tasks for this wing
        tasks_data = await apps_get("Tasks", wing=wing_name, guild=guild)
        tasks = [t for t in tasks_data[1:] if len(t) > 7 and t[7] == wing_name and t[3] != "Deleted"] if tasks_data and len(tasks_data) > 1 else []
        
        # Get Vision Plans for this wing
        vision_data = await apps_get("VisionPlans", wing=wing_name, guild=guild)
        vision_plans = [v for v in vision_data[1:] if len(v) > 7 and v[1] == wing_name and v[7] == "Active"] if vision_data and len(vision_data) > 1 else []
        
        # Calculate metrics
        metrics = calculate_wing_metrics(tasks)
        
        # Separate tasks and plans
        weekly_tasks = [t for t in tasks if len(t) > 12 and t[12] == "Weekly"]
        monthly_tasks = [t for t in tasks if len(t) > 12 and t[12] == "Monthly"]
        
        weekly_vision = next((v for v in vision_plans if v[2] == "Weekly"), None)
        monthly_vision = next((v for v in vision_plans if v[2] == "Monthly"), None)

        async def update_dashboard(period_type, tasks_list, vision_plan, msg_id_index, payload_key):
            embed = discord.Embed(
                title=f"📊 {wing_name} Wing - {period_type} Dashboard",
                description=f"{period_type} Overview for {datetime.now(timezone.utc).strftime('%B %Y')}",
                color=discord.Color.blue() if period_type == "Weekly" else discord.Color.dark_purple(),
                timestamp=datetime.now(timezone.utc)
            )

            # Add Vision Plan if exists
            if vision_plan:
                vision_stmt = vision_plan[3]
                targets_raw = vision_plan[4]
                targets_fmt = "\n".join([f"🎯 {t.strip()}" for t in targets_raw.split('\n') if t.strip()])
                embed.add_field(name="🌟 Vision", value=f"_{vision_stmt}_", inline=False)
                embed.add_field(name="📍 Targets", value=targets_fmt or "None", inline=False)

            # Active goals/tasks
            active = [t for t in tasks_list if t[3] != "Done"][:5]
            if active:
                goals_text = ""
                for t in active:
                    title = t[1]
                    if len(t) > 16 and t[15] == "Percentage" and t[16]:
                        try:
                            percentage = int(t[16])
                            progress = create_progress_bar(percentage, 8)
                            goals_text += f"├─ {title} {progress}\n"
                        except: goals_text += f"├─ {title}\n"
                    else:
                        goals_text += f"├─ {title}\n"
                embed.add_field(name="📝 Active Goals", value=goals_text or "None", inline=False)

            # Metrics for this period
            done_count = len([t for t in tasks_list if t[3] == "Done"])
            total_count = len(tasks_list)
            rate = round((done_count / total_count) * 100) if total_count > 0 else 0
            embed.add_field(
                name="📈 Period Metrics",
                value=f"Completed: {done_count}/{total_count} ({rate}%)\nIn Progress: {len([t for t in tasks_list if t[3] == 'InProgress'])}",
                inline=False
            )

            # Update Message
            msg_id = wing_showcase[msg_id_index] if len(wing_showcase) > msg_id_index and wing_showcase[msg_id_index] else None
            if msg_id:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.edit(embed=embed)
                except:
                    msg = await channel.send(embed=embed)
                    await apps_post("WingShowcaseUpdate", {"wing": wing_name, payload_key: str(msg.id)})
            else:
                msg = await channel.send(embed=embed)
                await apps_post("WingShowcaseUpdate", {"wing": wing_name, payload_key: str(msg.id)})

        # Update both Weekly and Monthly
        await update_dashboard("Weekly", weekly_tasks, weekly_vision, 2, "weekly_message_id")
        await update_dashboard("Monthly", monthly_tasks, monthly_vision, 3, "monthly_message_id")

        # Update General metrics in sheet
        completed_this_week = [t for t in tasks if t[3] == "Done" and len(t) > 11]
        update_payload = {
            "wing": wing_name,
            "last_updated": str(datetime.now(timezone.utc)),
            "active_tasks_count": metrics['total'],
            "completed_this_week": len(completed_this_week),
            "completion_rate": metrics['completion_rate']
        }
        await apps_post("WingShowcaseUpdate", update_payload)
        
    except Exception as e:
        print(f"Error updating wing showcase for {wing_name}: {e}")

async def update_task_message(guild, task_id, new_progress):
    """Update the original task message with new progress, status, and colors"""
    try:
        tasks_data = await apps_get("Tasks", guild=guild)
        if not tasks_data or len(tasks_data) < 2:
            return
        
        task = None
        for t in tasks_data[1:]:
            if str(t[0]) == str(task_id):
                task = t
                break
        
        if not task or not task[9]:  # No message_id
            return
        
        message_id = int(task[9])
        channel_id = int(task[23]) if len(task) > 23 and task[23] else None
        
        msg = None
        if channel_id:
            try:
                channel = guild.get_channel(channel_id) or await bot.fetch_channel(channel_id)
                if channel:
                    msg = await channel.fetch_message(message_id)
            except: pass
            
        if not msg:
            for channel in guild.text_channels:
                try:
                    msg = await channel.fetch_message(message_id)
                    if msg: break
                except: continue
        
        if not msg or not msg.embeds:
            return

        status = task[3]
        priority = task[8]
        metric_type = task[15]
        metric_current = task[16]
        metric_total = task[17]
        metric_unit = task[18]
        
        assignee_name = task[6]
        owner_name = task[5]
        
        # Try to resolve names to mentions
        assignee_mention = assignee_name
        owner_mention = owner_name
        
        # This is a bit expensive but necessary for proper mentions
        # We try to find members by name
        for mem in guild.members:
            if mem.name == assignee_name:
                assignee_mention = mem.mention
            if mem.name == owner_name:
                owner_mention = mem.mention
        
        color_map = {"High": discord.Color.red(), "Medium": discord.Color.gold(), "Low": discord.Color.green(), "Done": discord.Color.green()}
        embed_color = color_map.get("Done" if status == "Done" else priority, discord.Color.gold())
        
        old_embed = msg.embeds[0]
        new_embed = discord.Embed(
            title=old_embed.title,
            description=old_embed.description,
            color=embed_color
        )
        
        for field in old_embed.fields:
            if field.name == "Status":
                new_embed.add_field(name="Status", value=status, inline=True)
            elif field.name == "Assigned To":
                new_embed.add_field(name="Assigned To", value=assignee_mention, inline=True)
            elif field.name == "Owner":
                new_embed.add_field(name="Owner", value=owner_mention, inline=True)
            elif field.name == "📊 Progress" or field.name == "📊 Metric":
                continue
            else:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
        
        if metric_type == "Percentage":
            try:
                # Use float first to handle cases like "50.0" as string
                pct = int(float(metric_current))
                new_embed.add_field(name="📊 Progress", value=create_progress_bar(pct), inline=False)
            except: pass
        elif metric_type == "Count":
            new_embed.add_field(name="📊 Progress", value=f"{metric_current}/{metric_total} {metric_unit}", inline=False)
        elif metric_type == "Custom":
            new_embed.add_field(name="📊 Metric", value=f"{metric_unit}: {metric_current}", inline=False)
            
        new_embed.set_footer(text=old_embed.footer.text if old_embed.footer else "")
        if not any(f.name == "Status" for f in new_embed.fields):
             new_embed.add_field(name="Status", value=status, inline=True)

        await msg.edit(embed=new_embed)
        
    except Exception as e:
        print(f"Error updating task message: {e}")
