import discord
from discord.ext import commands
from discord import SlashCommandGroup, Option
import ezcord



class Config(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.radio_senders = {
            "Iloveradio": "https://ilm-stream12.radiohost.de/ilm_iloveradio_mp3-192?_art=dD0xNzMxMjMxNzM4JmQ9MjIwODc3MzBmOWRmZTVmZTg1OGY",
            "Ilovedance": "https://ilm-stream18.radiohost.de/ilm_ilove2dance_mp3-192?_art=dD0xNzMxMjMxNzU2JmQ9MWE5MGVmM2YzZWNiOGVhM2I2NWU",
            "Ilovehiphop": "https://ilm.stream35.radiohost.de/ilm_hiphop-2023-jahrescharts_mp3-192?_art=dD0xNzMxMjMxNzg5JmQ9MzljZTE5MmE0ZGFkZTE2ZGNlMDM",
            "Ilovebass": "https://ilm-stream11.radiohost.de/ilm_ilovebass_mp3-192?_art=dD0xNzMyMjg5ODgyJmQ9N2RkYjNjYjhhY2ZmMmMxMDViMzc",
			"bollerwagen": "https://www.internetradio-horen.de/ffn-bollerwagen?gad_source=1&gclid=CjwKCAiA1eO7BhATEiwAm0Ee-Dyh_-Ro46UiPLrq-ci9wrnqeCAOQmbFJLtzG2WfQ5_xABDpkhIlXBoCqUUQAvD_BwE"
        }

    config = SlashCommandGroup("config", "Commands related to bot configuration")

    @config.command(name="overview")
    async def overview(self, ctx):
        embed = discord.Embed(
            title="🟢 | Bot Overview",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🤖 | Server Informationen",
            value="📻 | Radiosender: {radio_sender}"
        )
        await ctx.respond(embed=embed)

    @config.command(name="senders")
    async def senders(self, ctx):
        embed = discord.Embed(
            title="📻 | Verfügbare Radiosender",
            description="\n".join(self.radio_senders.keys()),
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed)

    @config.command(name="change_radio")
    async def change_radio(self, ctx, channel: discord.VoiceChannel, sender: str):
        
        if sender not in self.radio_senders:
            await ctx.respond("❌ | Dieser Sender ist nicht verfügbar. Bitte wähle einen der voreingestellten Sender.")
            return

        
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        voice_client = await channel.connect()

        
        radio_url = self.radio_senders[sender]
        voice_client.play(discord.FFmpegPCMAudio(source=radio_url))

       
        embed = discord.Embed(
            title="🔄 | Radio geändert",
            description=f"Der Radiosender im Kanal **{channel.name}** wurde auf **{sender}** geändert.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Config(bot))
