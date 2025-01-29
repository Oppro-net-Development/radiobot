import os
import discord
from discord.ext import commands, tasks
from discord import Option
import asyncio
import json
import aiohttp  


CHANNELS_FILE = 'channels.json'

class RadioCog(commands.Cog):
    """Enthält alle Funktionen und Befehle für das Radio-Feature."""

    def __init__(self, bot):
        self.bot = bot
        self.channel_cache = set()
       # self.check_connections.start()
        self.fetch_status.start()  

    async def cog_load(self):
        """Wird beim Laden des Cogs ausgeführt, wird aber nicht direkt aufgerufen."""
        pass

    async def on_ready(self):
        """Wird ausgeführt, wenn der Bot vollständig eingeloggt ist."""
        print("Bot ist bereit!")
        await self.load_channels()
        await self.connect_to_channels()

    async def load_channels(self):
        """Lädt die Kanalliste aus der JSON-Datei."""
        if not os.path.exists(CHANNELS_FILE):
            
            with open(CHANNELS_FILE, 'w') as f:
                json.dump([], f)
        
        with open(CHANNELS_FILE, 'r') as f:
            channels = json.load(f)
            self.channel_cache = set(channels)

        print(f"Geladene Kanäle: {self.channel_cache}")

    def save_channels(self):
        """Speichert die Kanalliste in der JSON-Datei, ohne bestehende IDs zu überschreiben."""
        with open(CHANNELS_FILE, 'r') as f:
            existing_channels = json.load(f)

        
        updated_channels = list(set(existing_channels) | self.channel_cache)

        with open(CHANNELS_FILE, 'w') as f:
            json.dump(updated_channels, f)

    async def add_channel(self, channel_id):
        """Fügt einen Kanal zur JSON-Datei und zum Cache hinzu."""
        if channel_id not in self.channel_cache:
            self.channel_cache.add(channel_id)
            self.save_channels()

    async def remove_channel(self, channel_id):
        """Entfernt einen Kanal aus der JSON-Datei und dem Cache."""
        if channel_id in self.channel_cache:
            self.channel_cache.remove(channel_id)
            self.save_channels()

    async def connect_to_channels(self):
        """Verbindet den Bot mit allen gespeicherten Kanälen."""
        print("Überprüfe gespeicherte Kanäle...")
        for channel_id in self.channel_cache:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"Fehler: Kanal mit ID {channel_id} nicht gefunden.")
                continue

            if isinstance(channel, discord.VoiceChannel):
                await self.connect_and_play(channel)

    async def connect_and_play(self, channel):
        """Verbindet den Bot mit einem Kanal und startet die Wiedergabe."""
        print(f"Versuche, den Kanal {channel.name} zu betreten...")
        try:
            
            voice_client = channel.guild.voice_client
            if voice_client:
                if voice_client.channel != channel:
                    print(f"Bot ist bereits in einem Kanal: {voice_client.channel.name}, wechsle zu {channel.name}")
                    await voice_client.disconnect()
            
            
            if not channel.guild.voice_client:
                await channel.connect()
            
            voice_client = channel.guild.voice_client

            if voice_client and not voice_client.is_playing():
                await self.play_next(channel)
        except discord.errors.ClientException as e:
            print(f"Fehler beim Verbinden zu {channel.name}: {e}")
            await asyncio.sleep(5)  
        except Exception as e:
            print(f"Unbekannter Fehler bei der Verbindung zu {channel.name}: {e}")

    async def play_next(self, channel):
        """Startet die nächste Wiedergabe."""
        voice_client = channel.guild.voice_client
        if voice_client:
            try:
                if not voice_client.is_playing():
                    voice_client.play(discord.FFmpegPCMAudio("https://ilm-stream11.radiohost.de/ilm_ilovebass_mp3-192"))
            except Exception as e:
                print(f"Fehler beim Starten der Wiedergabe: {e}")
                await asyncio.sleep(5)
                await self.play_next(channel)



    @tasks.loop(seconds=20)
    async def fetch_status(self):
        """Sendet regelmäßig ein Status-Update an die angegebene URL."""
        await self.bot.wait_until_ready()  
        url = 'http://node4.yourhoster.tech:5561/api/push/KaZBYXvx22?status=up&msg=OK&ping='
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    print()
                else:
                    print(f'Fehler beim Senden des Status-Updates: {response.status}')

    @commands.slash_command(name="setradio", description="Fügt einen Sprachkanal zur Radio-Liste hinzu")
    async def set_radio(self, ctx, channel: Option(discord.VoiceChannel, "Wähle einen Sprachkanal")):
        await self.add_channel(channel.id)
        await self.connect_and_play(channel)
        await ctx.respond(f"🔊 Kanal **{channel.name}** wurde zur Radio-Liste hinzugefügt!")

    @commands.slash_command(name="removeradio", description="Entfernt einen Sprachkanal aus der Radio-Liste")
    async def remove_radio(self, ctx, channel: Option(discord.VoiceChannel, "Wähle einen Sprachkanal")):
        await self.remove_channel(channel.id)
        if channel.guild.voice_client and channel.guild.voice_client.channel == channel:
            await channel.guild.voice_client.disconnect()
        await ctx.respond(f"🛑 Kanal **{channel.name}** wurde aus der Radio-Liste entfernt!")

    @commands.slash_command(name="leaderboard", description="Zeigt ein Leaderboard aller Server und deren Mitgliederzahlen an.")
    async def leaderboard(self, ctx):
        servers = [(guild.name, guild.member_count) for guild in self.bot.guilds]
        sorted_servers = sorted(servers, key=lambda x: x[1], reverse=True)
        leaderboard_message = "**📊 Server Leaderboard**\n\n"
        for rank, (server_name, member_count) in enumerate(sorted_servers[:10], start=1):
            leaderboard_message += f"{rank}. {server_name[:20]}...: {member_count} Mitglieder\n"
        await ctx.respond(leaderboard_message, ephemeral=True)

def setup(bot):
    bot.add_cog(RadioCog(bot))
