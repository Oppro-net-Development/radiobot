import discord
import os
import psutil
import sys
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime, timedelta

load_dotenv()
DEVELOPER_IDS = [int(id.strip()) for id in os.getenv("DEVELOPER_IDS").split(",")]

db = sqlite3.connect('status.db')
cursor = db.cursor()

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS status_message (id INTEGER PRIMARY KEY, message_id INTEGER, channel_id INTEGER)''')
db.commit()


class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_status = "🔴 Offline"
        self.start_time = datetime.utcnow()
        self.status_message = None
        self.command_usage = {"24h": 0, "7d": 0, "30d": 0, "total": 0}
        self.member_history = {"24h": 0, "7d": 0, "30d": 0}
        self.server_history = {"24h": 0, "7d": 0, "30d": 0}

        self.update_member_server_stats.start()
        self.update_embed.start()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot_status = "🟢 Online"
        await self.update_member_server_stats()

        cursor.execute('SELECT message_id, channel_id FROM status_message ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()

        if result:
            message_id, channel_id = result

            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    self.status_message = await channel.fetch_message(message_id)
                    print(f"Status embed nach Neustart geladen und wird aktualisiert.")
                except discord.NotFound:
                    print("Gespeicherte Nachricht nicht gefunden. Eine neue wird erstellt.")
            else:
                print("Channel nicht gefunden, eine neue Nachricht wird erstellt.")
        else:
            print("Keine gespeicherte Nachricht gefunden, eine neue wird erstellt.")

    @commands.Cog.listener()
    async def on_connect(self):
        self.bot_status = "🟠 Starting up"

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.bot_status = "🔴 Offline"

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.command_usage["total"] += 1
        self.command_usage["24h"] += 1
        self.command_usage["7d"] += 1
        self.command_usage["30d"] += 1

    @tasks.loop(seconds=30)
    async def update_member_server_stats(self):
        current_members = sum(guild.member_count for guild in self.bot.guilds)
        current_servers = len(self.bot.guilds)

        self.member_history["24h"] = current_members - self.member_history.get("total", current_members)
        self.member_history["7d"] = current_members - self.member_history.get("total", current_members)
        self.member_history["30d"] = current_members - self.member_history.get("total", current_members)

        self.server_history["24h"] = current_servers - self.server_history.get("total", current_servers)
        self.server_history["7d"] = current_servers - self.server_history.get("total", current_servers)
        self.server_history["30d"] = current_servers - self.server_history.get("total", current_servers)

        self.member_history["total"] = current_members
        self.server_history["total"] = current_servers

    def get_uptime(self):
        delta = datetime.utcnow() - self.start_time
        days, seconds = delta.days, delta.seconds
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        uptime_string = ""

        if days > 0:
            uptime_string += f"{days}d "
        if hours > 0 or days > 0:
            uptime_string += f"{hours}h "
        if minutes > 0 or hours > 0 or days > 0:
            uptime_string += f"{minutes}m "

        uptime_string += f"{seconds}s"
        return uptime_string

    def get_server_stats(self):
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "CPU": f"{cpu}%",
            "Memory": f"{memory.percent}%",
            "Disk": f"{disk.percent}%"
        }

    async def create_status_embed(self):
        ping = round(self.bot.latency * 1000)
        discord_api_ping = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="💻 Bot Status Overview",
            color=discord.Color.green() if self.bot_status == "🟢 Online" else discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="⚙️ Bot Info",
                        value=f"**Status**: {self.bot_status} | ⏳ **Uptime**: {self.get_uptime()}  | 📶 **Ping**: `{ping}`ms  | 🌐 **API Ping**: `{discord_api_ping}`ms ",
                        inline=False)
        embed.add_field(
            name="📊 Bot Statistics",
            value=f"👥 **Members**: {self.member_history['total']}  |🌐 **Servers**: {self.server_history['total']} ",
            inline=False
        )
        embed.add_field(name="🖱️ Command Usage",
                        value=f"**24h**: {self.command_usage['24h']} | **7d**: {self.command_usage['7d']} | **30d**: {self.command_usage['30d']} | **Total**: {self.command_usage['total']}",
                        inline=False)

        server_stats = self.get_server_stats()
        embed.add_field(
            name="🖥️ Hosting Server",
            value=f"🧑‍💻**CPU**: {server_stats['CPU']} |💾 **Memory**: {server_stats['Memory']}  | 🗂️ **Disk**: {server_stats['Disk']}",
            inline=False
        )

        return embed

    @tasks.loop(seconds=30)
    async def update_embed(self):
        if self.status_message:
            embed = await self.create_status_embed()
            try:
                await self.status_message.edit(embed=embed)
            except discord.errors.NotFound:
                print("Die Nachricht konnte nicht gefunden werden, wahrscheinlich gelöscht.")
                self.status_message = None

    @commands.slash_command(name="status", description="Zeigt den aktuellen Bot-Status an")
    async def status(self, ctx):
        if ctx.author.id not in DEVELOPER_IDS:
            await ctx.respond("🚫 Du hast keine Berechtigung für diesen Befehl.", ephemeral=True)
            return

        embed = await self.create_status_embed()
        if self.status_message is None:
            self.status_message = await ctx.send(embed=embed)
            cursor.execute('INSERT INTO status_message (message_id, channel_id) VALUES (?, ?)',
                           (self.status_message.id, self.status_message.channel.id))
            db.commit()
        else:
            try:
                await self.status_message.edit(embed=embed)
            except discord.errors.NotFound:
                self.status_message = await ctx.send(embed=embed)
                cursor.execute('INSERT INTO status_message (message_id, channel_id) VALUES (?, ?)',
                               (self.status_message.id, self.status_message.channel.id))
                db.commit()

        await ctx.respond("✅ Das Status-Embed wird regelmäßig aktualisiert.", ephemeral=True)

    @commands.slash_command(name="restart", description="Startet den Bot neu und zeigt den aktuellen Status an")
    async def restart(self, ctx):
        if ctx.author.id not in DEVELOPER_IDS:
            await ctx.respond("🚫 Du hast keine Berechtigung für diesen Befehl.", ephemeral=True)
            return

        await ctx.respond("🔄 Bot wird neu gestartet...")
        os.execv(sys.executable, ['python'] + sys.argv)


def setup(bot):
    bot.add_cog(StatusCog(bot))