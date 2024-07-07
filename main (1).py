import discord
from discord.ext import commands, tasks
from discord import slash_command, Option
import asyncio
import sqlite3

# Datenbank einrichten
DATABASE = 'radio_channels.db'

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
    c.execute('INSERT INTO channels (id) VALUES (?)', (channel_id,))
    conn.commit()
    conn.close()

def remove_channel(channel_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
    conn.commit()
    conn.close()

# Token als Umgebungsvariable oder direkt im Skript (nur zu Testzwecken)
TOKEN = "MTI0OTY5NTg4MTQ5NDc5NDMwMQ.G-s0Vq.eE6f_LL6PI7SnCZ16DuGWWRLqHULLTVFTE1tB0"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

initial_channels = set()

@bot.event
async def on_ready():
    global initial_channels
    print("Bot is ready. Attempting to connect to voice channels...")
    initial_channels = set(get_channels())  # Aktuelle Kanäle aus der Datenbank laden
    for channel_id in initial_channels:
        try:
            channel = bot.get_channel(channel_id)
            if isinstance(channel, discord.VoiceChannel):
                await connect_and_play(channel)
            else:
                print(f"Channel ID {channel_id} is not a voice channel.")
        except Exception as e:
            print(f"Fehler beim Verbinden zu Kanal {channel_id}: {e}")
    
    check_music.start()
    print("The Radio is online!")

async def connect_and_play(channel):
    try:
        if channel.guild.voice_client:  # Falls bereits verbunden, vorherige Verbindung trennen
            await channel.guild.voice_client.disconnect()

        voice_client = await channel.connect()
        voice_client.play(discord.FFmpegPCMAudio("https://streams.ilovemusic.de/iloveradio16.mp3"))
        print(f"Connected and playing music in {channel.name}.")
    except Exception as e:
        print(f"Fehler beim Abspielen von Musik in {channel.name}: {e}")

@tasks.loop(minutes=5)  # Prüfen alle 5 Minuten
async def check_music():
    current_channels = set(get_channels())  # Aktuelle Kanäle aus der Datenbank laden
    if current_channels != initial_channels:
        print("Channel list has changed. Restarting bot...")
        await restart_bot()

@bot.command()
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Restarting bot...")
    await bot.close()
    await asyncio.sleep(1)
    await bot.start(TOKEN)

async def restart_bot():
    await bot.close()
    await asyncio.sleep(1)
    await bot.start(TOKEN)

@bot.slash_command(name="setradio", description="Fügt einen Sprachkanal zur Radio Liste hinzu")
async def set_radio(ctx, channel: discord.VoiceChannel):
    add_channel(channel.id)
    await ctx.send(f"Channel ID {channel.id} added to the radio list.")
    await restart_bot()

@bot.slash_command(name="removeradio", description="Entfernt einen Sprachkanal aus der Radio Liste")
async def remove_radio(ctx, channel: discord.VoiceChannel):
    remove_channel(channel.id)
    await ctx.send(f"Channel ID {channel.id} removed from the radio list.")

init_db()
bot.run(TOKEN)
