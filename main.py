import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
import asyncio
from itertools import cycle

load_dotenv(".env")
TOKEN: str = os.getenv('TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

bot_statuses = cycle(["Me hungry", "Me sleppy", "Minecraft", "Baba Booey"])

@tasks.loop(seconds=60)
async def change_bot_status():
 await bot.change_presence(activity=discord.Game(next(bot_statuses)))

@bot.event
async def on_ready():
 print("Bot ready!")
 change_bot_status.start()
 try:
  synced_commands = await bot.tree.sync()
  print(f"Synced {len(synced_commands)} commands.")
 except Exception as e:
  print("An error with syncing application commands has occurred: ", e)

async def load():
 for filename in os.listdir("./cogs"):
  if filename.endswith(".py"):
   await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
 async with bot:
  await load()
  await bot.start(TOKEN)

asyncio.run(main())
