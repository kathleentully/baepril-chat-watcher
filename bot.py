from dotenv import load_dotenv
import datetime
import discord
from discord.ext import commands
from math import floor
from os import getenv
from random import choice
import traceback 

# .env file format
# TOKEN=
# DEBUG_MODE=
# GUILD_ID=
# LOG_CHANNEL=
# OUTPUT_CHANNEL=

load_dotenv()

COMMAND_PREFIX = '!'
MSG_SIZE_LIMIT = 1500
MSG_COUNT_LIMIT = 5
RECENT_TIMING = datetime.timedelta(days=1)

DEBUG_MODE = bool(getenv('DEBUG_MODE', 'False').lower() == 'true')
log_channel = None
output_channel = None
guild = None
bot = commands.Bot(command_prefix=COMMAND_PREFIX)


async def log(msg):
    if DEBUG_MODE:
        if log_channel:
            msg = str(msg)
            split_count = 0
            while len(msg) > 0 and split_count < MSG_COUNT_LIMIT:
                await log_channel.send(f'LOG: {msg[:MSG_SIZE_LIMIT]}')
                msg = msg[MSG_SIZE_LIMIT:]
                split_count += 1
        else:
            print(msg)


def log_function_call(func):
    async def wrapper(context=None, *args):
        await log(f'Received {context.prefix}{context.command} {args} from {context.message.author}')
        try:
            await func(context, *args)
        except Exception as e:
            traceback.print_exc() 
            await log(f'{context.prefix}{context.command} {args} from {context.message.author} FAILED:\n{e}\nStack trace logged')
    return wrapper


def time_since(timestamp):
    time_since = datetime.datetime.now(timestamp.tzinfo) - timestamp
    if time_since < datetime.timedelta(days=1):
        return 'today'
    if time_since < datetime.timedelta(days=2):
        return 'yesterday'
    if time_since < datetime.timedelta(days=7):
        return 'this week'
    if time_since < datetime.timedelta(days=14):
        return 'last week'
    if time_since < datetime.timedelta(days=70):
        return f'{int(time_since.days / 7)} weeks ago'
    if time_since < datetime.timedelta(days=365):
        return f'{int(time_since.days / 30)} months ago'
    return f'{int(time_since.days / 365.2425)} years ago'


async def print_threads():
    # r'<#(\d*)>'
    #if output_channel.

    all_channels = {}
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            try:
                archived_threads = await channel.archived_threads().next()
                if channel.threads or archived_threads:
                    all_channels[channel.position] = channel
            except (discord.NoMoreItems, discord.errors.Forbidden):
                pass

    for key in sorted(all_channels):
        channel = all_channels[key]
        message = ""
        recent_time = datetime.datetime.now((guild.created_at.tzinfo)) - RECENT_TIMING
        embeds = []
        for thread in channel.threads:
            if not thread.archived:
                async for thread_msg in channel.history(limit=1, oldest_first=True):
                    if thread_msg.created_at < recent_time:
                        # embeds.append(discord.Embed(title=f" - **{thread.name}** *(new)*", url=thread_msg.jump_url))
                        message += f'\n **- [{thread.name}]({thread_msg.jump_url})** *(new)*'
                        await log(f'\n **- [{thread.name}]({thread_msg.jump_url})** *(new)*')
                    else:
                        # embeds.append(discord.Embed(title=f" - {thread.name}", url=thread_msg.jump_url))
                        message += f'\n - [{thread.name}]({thread_msg.jump_url})'
                        await log(f'\n - [{thread.name}]({thread_msg.jump_url})')
        
        async for thread in channel.archived_threads():
            if thread.archived:
                message += f'\n *- {thread.name} (archived {time_since(thread.archive_timestamp)})*'
        if embeds:
            await output_channel.send(channel.mention)
            for embed in embeds:
                await output_channel.send(embed=embed)
            await output_channel.send(message)
        else:
            await output_channel.send(f"{channel.mention}{message}")


async def setup():
    if DEBUG_MODE:
        global log_channel
        log_channel_id = int(getenv("LOG_CHANNEL", 0))
        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
    global output_channel
    output_channel = bot.get_channel(int(getenv("OUTPUT_CHANNEL")))

    global guild
    guild = bot.get_guild(int(getenv("GUILD_ID")))

    if DEBUG_MODE:
        await log(f'Bot connected as {bot.user}')


@bot.event
async def on_ready():
    await setup()
    #for guild in bot.guilds:
    #    await log(f"{guild.name} - {guild.id}")
    #    for channel in guild.channels:
    #        await log(f"  * {channel.name} - {channel.id}")

    await print_threads()



bot.run(getenv("TOKEN"))