import discord
import ezcord
from discord.ext import tasks
import os
from dotenv import load_dotenv
import json
import asyncio


load_dotenv()


intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True

admin_server_ids = [1097205376740499466]


bot = ezcord.Bot(
    intents=intents,
    ready_event=ezcord.ReadyEvent.box_colorful,  
    language="en"  
)

if __name__ == "__main__":
    bot.load_cogs() 
    bot.add_help_command()
    bot.add_blacklist(admin_server_ids)
    bot.run()
