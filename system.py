import discord
from discord.ext import commands
from discord import slash_command, Option
import ezcord

# Übersetzungsdaten für Texte und Buttons
translations = {
    "joining": {
        "en": "Please use when you are sure that there are no more members in the channel. The bot can then enter or leave the channel.",
        "de": "Bitte nutzen, wenn sie sicher sind, dass kein Mitglied mehr im Channel ist. Der Bot kann dann den Channel betreten oder verlassen.",
        "fr": "Veuillez l'utiliser si vous êtes sûr qu'il n'y a plus de membre sur la chaîne. Le bot peut alors entrer ou quitter le canal.",
        "es": "Úselo si está seguro de que ya no hay un miembro en el canal. Luego, el bot puede entrar o salir del canal.",
        "it": "Usalo se sei sicuro che non ci sono più membri nel canale. Il bot può quindi entrare o uscire dal canale."
    },
    "buttons": {
        "join": {
            "en": "Join",
            "de": "Beitreten",
            "fr": "Rejoindre",
            "es": "Unirse",
            "it": "Unisciti"
        },
        "leave": {
            "en": "Leave",
            "de": "Verlassen",
            "fr": "Quitter",
            "es": "Dejar",
            "it": "Lascia"
        }
    },
    "button_messages": {
        "join": {
            "en": "The bot has joined the channel.",
            "de": "Der Bot ist dem Channel beigetreten.",
            "fr": "Le bot a rejoint le canal.",
            "es": "El bot ha unido al canal.",
            "it": "Il bot è entrato nel canale."
        },
        "leave": {
            "en": "The bot has left the channel.",
            "de": "Der Bot hat den Channel verlassen.",
            "fr": "Le bot a quitté le canal.",
            "es": "El bot ha dejado el canal.",
            "it": "Il bot ha lasciato il canale."
        },
        "no_channel": {
            "en": "You must be in a voice channel for the bot to join.",
            "de": "Du musst in einem Voice-Channel sein, damit der Bot beitreten kann.",
            "fr": "Vous devez être dans un canal vocal pour que le bot rejoigne.",
            "es": "Debes estar en un canal de voz para que el bot se una.",
            "it": "Devi essere in un canale vocale affinché il bot si unisca."
        },
        "not_in_channel": {
            "en": "The bot is not in any channel.",
            "de": "Der Bot ist momentan in keinem Channel.",
            "fr": "Le bot n'est dans aucun canal.",
            "es": "El bot no está en ningún canal.",
            "it": "Il bot non è in nessun canale."
        }
    }
}


class System(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Bot Settings")
    async def settings(self, ctx):
        lang = ctx.guild.preferred_locale if ctx.guild else "en"  # Standardmäßig auf Englisch setzen, kann aber angepasst werden
        # Hier kannst du die Sprache des Benutzers oder Servers ermitteln
        # Zum Beispiel:
        # lang = ctx.guild.preferred_locale if ctx.guild else "en"

        # Übersetzung des Textes basierend auf der ermittelten Sprache
        joining_text = translations["joining"].get(lang, translations["joining"]["en"])
        join_button_text = translations["buttons"]["join"].get(lang, translations["buttons"]["join"]["en"])
        leave_button_text = translations["buttons"]["leave"].get(lang, translations["buttons"]["leave"]["en"])

        embed = discord.Embed(
            title="Bot Settings",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Join and Leave",
            value=joining_text
        )
        await ctx.respond(embed=embed, view=Join(join_button_text, leave_button_text, lang))


def setup(bot):
    bot.add_cog(System(bot))


class Join(discord.ui.View):
    def __init__(self, join_text, leave_text, lang):
        super().__init__(timeout=None)
        self.join_text = join_text
        self.leave_text = leave_text
        self.lang = lang  # Die bevorzugte Sprache des Benutzers/Servers

    @discord.ui.button(label="Join", style=discord.ButtonStyle.green, custom_id="join_button")
    async def join_button(self, button, interaction):
        # Prüfen, ob der Benutzer in einem Voice-Channel ist
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if channel:
            await channel.connect()  # Bot tritt dem Channel bei
            join_message = translations["button_messages"]["join"].get(self.lang,
                                                                       translations["button_messages"]["join"]["en"])
            await interaction.response.send_message(join_message)
        else:
            no_channel_message = translations["button_messages"]["no_channel"].get(self.lang,
                                                                                   translations["button_messages"][
                                                                                       "no_channel"]["en"])
            await interaction.response.send_message(no_channel_message)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, custom_id="leave_button")
    async def leave_button(self, button, interaction):
        # Wenn der Bot in einem Voice-Channel ist, verlässt er den Channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            leave_message = translations["button_messages"]["leave"].get(self.lang,
                                                                         translations["button_messages"]["leave"]["en"])
            await interaction.response.send_message(leave_message)
        else:
            not_in_channel_message = translations["button_messages"]["not_in_channel"].get(self.lang, translations[
                "button_messages"]["not_in_channel"]["en"])
            await interaction.response.send_message(not_in_channel_message)
