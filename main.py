#Import modules
import discord
from discord.ext import commands
from discord.utils import get
import math
import datetime
import urllib.parse
import logging
import io
import os
from dotenv import load_dotenv

#Get config files
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONSOLE_CHANNEL = os.getenv("CONSOLE_CHANNEL")
PLAYLIST_FILE = os.getenv("PLAYLIST_FILE")

# Configure the logging module to capture Discord.py logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
log_buffer = io.StringIO()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

class DiscordLogHandler(logging.Handler):
    def emit(self, record):
        log_message = self.format(record)    
        # Clear the log buffer and store the latest log message
        log_buffer.truncate(0)
        log_buffer.seek(0)
        log_buffer.write(log_message)

discord_log_handler = DiscordLogHandler()
logger.addHandler(discord_log_handler)

from xspf_lib import Playlist
playlist = Playlist.parse(PLAYLIST_FILE)
tracklist = playlist.trackList
mainlist = []
for i in range(0, len(playlist)):
    song = tracklist[i]
    sub = [song.title, song.location[0].strip("file:///"), song.creator, song.album, song.duration, song.image]
    mainlist.append(sub)

selectedsong = None
vc = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    console_channel = await bot.fetch_channel(CONSOLE_CHANNEL)
    print(console_channel)
    message = """**Initializing the following commands: <a:loading:1153202857969983488> **
 ✔️ `!search <page>` - Accepted argument(s): `<page>` **(Non-Negative Integer)**
 ✔️ `!join` - Accepted argument(s): `None`
 ✔️ `!play <id>` - Accepted argument(s): `<id>` **(ID CAN BE RETURNED BY !SEARCH / Non-Negative Integer)**
 ✔️ `!stop` - Accepted argument(s): `None`
 ✔️ `!disconnect` - Accepted argument(s): `None` """
    if console_channel:
        await(console_channel.send(message))
        await console_channel.send(f'`Client initialized. Loaded {len(mainlist)} songs.`')

@bot.command()
async def search(ctx, page):
    songsperpage = 25
    if str(page).isnumeric():
        start = songsperpage * ((int(page) - 1))
        end = songsperpage * ((int(page)))
        if end > len(mainlist):
            end = len(mainlist)-1
        message = f""
        for i in range(start, end):
            message = message + f"`{i + 1}` - {mainlist[i][0]} `by {mainlist[i][2]}` \n"
    embed = discord.Embed(title=f"**Displaying songs {start} to {end}!**", description = message, color=discord.Color.from_rgb(255,187,187), timestamp=datetime.datetime.utcnow())
    embed.set_author(name=f"Page: {page}")
    embed.set_footer(text=f"To play a song, use `!play <id>`")
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You are not in a voice channel.")
        return  
    # Get the voice channel to play the audio in
    voice_channel = ctx.author.voice.channel
    # Join the voice channel
    vc = await voice_channel.connect()
    await ctx.send(f"Joined the voice channel: `{voice_channel}`")

@bot.command()
async def play(ctx, id):
    # Check if the bot is already in a voice channel
    if ctx.voice_client == None:
        await ctx.send("I'm not a voice channel yet. Use `!join` to add me in a voice channel!")
        return None 
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    # Load and play the local MP3 file
    await ctx.send("Fetching song data... Please wait! <a:loading:1153202857969983488>")
    imgpath = (urllib.parse.unquote(mainlist[int(id) - 1][5])).replace("file:///",'')
    seconds = math.floor((int(mainlist[int(id) - 1][4])/1000))
    duration = str(datetime.timedelta(seconds=seconds))
    details = f"""`Artist`    : {mainlist[int(id) - 1][2]}
`Album`     : {mainlist[int(id) - 1][3]}
`Duration`  : {duration}"""
    
    #Create embed
    file = discord.File(imgpath, filename='art.png')
    embed = discord.Embed(title=f"{mainlist[int(id) - 1][0]}", description = details, color=discord.Color.from_rgb(255,187,187), timestamp=datetime.datetime.utcnow())
    embed.set_thumbnail(url='attachment://art.png')
    embed.set_author(name="Currently Playing")
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send("`Fetch successful ✓`. Awaiting playback...")
    await ctx.send(file=file, embed=embed)

    audio_source = discord.FFmpegPCMAudio(mainlist[int(id) - 1][1])
    ctx.voice_client.play(audio_source)

@bot.command()
async def stop(ctx):
    # Check if the bot is in a voice channel and playing audio
    if ctx.voice_client is not None and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("`Audio playback stopped.`")
    else:
        await ctx.send("I'm not playing audio right now.")

@bot.command()
async def disconnect(ctx):
    # Check if the bot is in a voice channel
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send("I have disconnected from the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command()
async def get_last_log(ctx):
    # Get the last log message from the log buffer
    last_log = log_buffer.getvalue()
    await ctx.send(f'```python\n{last_log}\n```')

@bot.command()
async def info(ctx):
    message = """**These are the available commands:**
  ✦ `!search <page>` - Accepted argument(s): `<page>` **(Non-Negative Integer)**
  ✦ `!join` - Accepted argument(s): `None`
  ✦ `!play <id>` - Accepted argument(s): `<id>` **(ID CAN BE RETURNED BY !SEARCH / Non-Negative Integer)**
  ✦ `!stop` - Accepted argument(s): `None`
  ✦ `!disconnect` - Accepted argument(s): `None` """
    await ctx.send(message)
    
bot.run(TOKEN)