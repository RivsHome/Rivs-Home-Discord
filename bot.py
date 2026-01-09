import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} connected!')

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hi {ctx.author.mention}, your personal agent is here!')

# Add personal features like task reminders here

import calendar_utils
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ... existing commands ...

@bot.command(name='schedule')
async def schedule(ctx, *, arg_str):
    """
    Schedules an event. 
    Usage: !schedule <Event Name> at <Time>
    Example: !schedule Team Meeting at tomorrow 2pm
    """
    if ' at ' not in arg_str:
        await ctx.send("Please use the format: `!schedule <Event Name> at <Time>`")
        return

    summary, time_str = arg_str.split(' at ', 1)
    
    await ctx.send(f"Scheduling '{summary}' at '{time_str}'...")
    
    try:
        event, error = calendar_utils.create_event(summary, time_str)
        if error:
            await ctx.send(f"Error: {error}")
        else:
            link = event.get('htmlLink')
            await ctx.send(f"Event created! Check it out here: {link}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name='events')
async def events(ctx, *, date_str=None):
    """
    Shows events.
    Usage: !events [tomorrow/today/date]
    Example: !events, !events tomorrow
    """
    await ctx.send("Fetching events...")
    try:
        events_list, error = calendar_utils.list_upcoming_events(date_str)
        
        # Fallback if date parsing fails
        if error and "parse date" in error:
            await ctx.send(f"⚠️ I couldn't understand '{date_str}' as a date. Showing next 10 upcoming events instead:")
            events_list, error = calendar_utils.list_upcoming_events(None)

        if error:
            await ctx.send(f"Error: {error}")
            return

        if not events_list:
            await ctx.send("No upcoming events found.")
            return

        response = "**Upcoming Events:**\n"
        for event in events_list:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            response += f"- **{summary}**: {start}\n"
            
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

class ScheduleModal(discord.ui.Modal, title='Schedule New Event'):
    event_name = discord.ui.TextInput(label='Event Name', placeholder='e.g. Team Meeting')
    event_time = discord.ui.TextInput(label='Time', placeholder='e.g. tomorrow at 2pm')

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # Acknowledge to prevent timeout
        
        summary = self.event_name.value
        time_str = self.event_time.value
        
        try:
            event, error = calendar_utils.create_event(summary, time_str)
            if error:
                await interaction.followup.send(f"Error: {error}", ephemeral=True)
            else:
                link = event.get('htmlLink')
                await interaction.followup.send(f"✅ Event created! [View on Calendar]({link})", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="Upcoming Events", style=discord.ButtonStyle.primary, emoji="📅")
    async def upcoming_events(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        events_list, error = calendar_utils.list_upcoming_events(None)
        if error:
             await interaction.followup.send(f"Error: {error}", ephemeral=True)
             return
             
        if not events_list:
            await interaction.followup.send("No upcoming events found.", ephemeral=True)
            return

        response = "**Upcoming Events:**\n"
        for event in events_list:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            response += f"- **{summary}**: {start}\n"
            
        await interaction.followup.send(response, ephemeral=True)

    @discord.ui.button(label="New Event", style=discord.ButtonStyle.success, emoji="➕")
    async def new_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ScheduleModal())

@bot.command(name='dashboard')
async def dashboard(ctx):
    """
    Shows the interactive dashboard.
    """
    await ctx.send("Welcome to your Personal Agent Dashboard:", view=DashboardView())

keep_alive()
bot.run(TOKEN)
