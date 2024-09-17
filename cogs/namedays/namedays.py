import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import mariadb
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME")
    )

class Namedays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.general_channel_id = int(os.getenv("GENERAL_CHANNEL_ID"))

        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

        self.namedays_announcement.start()

    @tasks.loop(hours=24)
    async def namedays_announcement(self):
        channel = self.bot.get_channel(self.general_channel_id)
        await self.send_namedays(channel)

    @namedays_announcement.before_loop
    async def before_namedays_announcement(self):
        await self.bot.wait_until_ready()

        now = datetime.utcnow() + timedelta(hours=3)
        future = now.replace(hour=6, minute=0, second=0, microsecond=0)

        if now >= future:
            future += timedelta(days=1)

        await discord.utils.sleep_until(future)

    def fetch_namedays(self, date):
        self.cursor.execute("""
            SELECT country, names
            FROM namedays
            WHERE date = ?;
        """, (date,))
        return self.cursor.fetchall()

    async def send_namedays(self, channel):
        today = (datetime.utcnow() + timedelta(hours=3)).strftime("%m.%d.")
        rows = self.fetch_namedays(today)

        names = {"lv": "", "lt": "", "ee": ""}

        for country, names_str in rows:
            names[country] = names_str

        response = ""
        for country, names_str in names.items():
            if names_str:
                country_name = {
                    "lv": "Latvian",
                    "lt": "Lithuanian",
                    "ee": "Estonian"
                }[country]
                response += f"**{country_name} Name Days:** {names_str}\n"

        if response:
            await channel.send(f"**Name Days for {today}**\n{response}")
        else:
            await channel.send(f"No name days today for {today}!")

    @app_commands.command(name="namedays", description="Get Baltic name days for today")
    async def namedays(self, interaction: discord.Interaction):
        today = (datetime.utcnow() + timedelta(hours=3)).strftime("%m.%d.")
        rows = self.fetch_namedays(today)

        names = {"lv": "", "lt": "", "ee": ""}

        for country, names_str in rows:
            names[country] = names_str

        response = ""
        for country, names_str in names.items():
            if names_str:
                country_name = {
                    "lv": "Latvian",
                    "lt": "Lithuanian",
                    "ee": "Estonian"
                }[country]
                response += f"**{country_name} Name Days:** {names_str}\n"

        if response:
            await interaction.response.send_message(response, ephemeral=True)
        else:
            await interaction.response.send_message(f"No name days today for {today}!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Namedays(bot))
