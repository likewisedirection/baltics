import json
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Namedays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="namedays", description="Get Latvian name days for today")
    async def namedays(self, interaction: discord.Interaction):
        # Get today's date
        today = datetime.today()
        current_month = today.month
        current_day = today.day

        # Load the namedays.json file
        with open("cogs/namedays/namedays.json", "r", encoding="utf-8") as file:
            namedays_data = json.load(file)

        # Filter names for today's month and day, where "include" is "1"
        names_today = [
            entry['name']
            for entry in namedays_data
            if entry['month'] == str(current_month) and entry['day'] == str(current_day) and>
        ]

        if names_today:
            names_str = ", ".join(names_today)
            await interaction.response.send_message(f"Today's Latvian name days are: {names_>
        else:
            await interaction.response.send_message("No name days today!")

async def setup(bot):
    await bot.add_cog(Namedays(bot))
