import discord
from discord.ext import commands, tasks
from discord import slash_command, Option
import asyncio
import sqlite3
import time
import os

# Datenbank einrichten
DATABASE = 'radio_channels.db'

# Globale Variable für die Startzeit
start_time = time.time()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id FROM channels')
    channels = [row[0] for row in c.fetchall()]
    conn.close()
    return channels

def add_channel(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO channels (id) VALUES (?)', (channel_id,))
    conn.commit()
    conn.close()

def remove_channel(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
    conn.commit()
    conn.close()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True  # Wichtig für die Mitgliederzählung

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Bot ist bereit. Versuche, mich mit Sprachkanälen zu verbinden...")
    await connect_to_channels()
    check_connections.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ILoveradio | Hosted by https://dash.samba-discord.de/register?ref=Y88dnPTB"))
    print("Das Radio ist online!")

async def connect_to_channels():
    for channel_id in get_channels():
        channel = bot.get_channel(channel_id)
        if isinstance(channel, discord.VoiceChannel):
            await connect_and_play(channel)
        else:
            print(f"Kanal-ID {channel_id} ist kein Sprachkanal.")

async def connect_and_play(channel):
    try:
        if channel.guild.voice_client:
            await channel.guild.voice_client.move_to(channel)
        else:
            await channel.connect()

        voice_client = channel.guild.voice_client
        if not voice_client.is_playing():
            await play_next(channel)

        await update_bot_status()
        print(f"Verbunden und spiele Musik in {channel.name}.")
    except Exception as e:
        print(f"Fehler beim Abspielen von Musik in {channel.name}: {e}")

async def play_next(channel):
    voice_client = channel.guild.voice_client
    if voice_client:
        try:
            voice_client.play(discord.FFmpegPCMAudio("https://ilm-stream18.radiohost.de/ilm_ilovebass_mp3-192?_art=dD0xNzI5NTI2Mjc2JmQ9YTQ5MDIxMDJhZTlkMGFkYWJkZjE"),
                              after=lambda e: asyncio.run_coroutine_threadsafe(play_next(channel), bot.loop))
            await update_bot_status()
        except Exception as e:
            print(f"Fehler beim Starten der nächsten Wiedergabe: {e}")
            await asyncio.sleep(5)  # Warte 5 Sekunden vor dem nächsten Versuch
            await play_next(channel)

async def update_bot_status():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ILoveradio"))

@tasks.loop(seconds=10)
async def check_connections():
    for channel_id in get_channels():
        channel = bot.get_channel(channel_id)
        if isinstance(channel, discord.VoiceChannel):
            if not channel.guild.voice_client or not channel.guild.voice_client.is_connected():
                await connect_and_play(channel)
            elif channel.guild.voice_client.channel != channel:
                await channel.guild.voice_client.move_to(channel)
                await play_next(channel)
            elif not channel.guild.voice_client.is_playing():
                await play_next(channel)
            await update_bot_status()

@bot.slash_command(name="setradio", description="Fügt einen Sprachkanal zur Radio-Liste hinzu")
async def set_radio(ctx, channel: Option(discord.VoiceChannel, "Wähle einen Sprachkanal")):
    add_channel(channel.id)
    await connect_and_play(channel)
    await ctx.respond(f"Kanal {channel.name} wurde zur Radio-Liste hinzugefügt.")

@bot.slash_command(name="removeradio", description="Entfernt einen Sprachkanal aus der Radio-Liste")
async def remove_radio(ctx, channel: Option(discord.VoiceChannel, "Wähle einen Sprachkanal")):
    remove_channel(channel.id)
    if channel.guild.voice_client and channel.guild.voice_client.channel == channel:
        await channel.guild.voice_client.disconnect()
    await ctx.respond(f"Kanal {channel.name} wurde aus der Radio-Liste entfernt.")
    
    await ctx.respond(embed=embed)

init_db()
if __name__ == "__main__":
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
bot.run(os.getenv("TOKEN"))