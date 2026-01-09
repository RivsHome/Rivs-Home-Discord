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

bot.run(TOKEN)
