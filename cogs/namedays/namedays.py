import csv
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Namedays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="namedays", description="Get Baltic name days for today")
    async def namedays(self, interaction: discord.Interaction):
        # Get today's date in the format "dd.mm."
        today = datetime.today()
        current_date = today.strftime("%d.%m.")

        # Initialize variables to store today's name days for each country
        names_lv = ""
        names_lt = ""
        names_ee = ""

        # Define the file paths
        files = {
            "Latvian": "cogs/namedays/namedays_lv.csv",
            "Lithuanian": "cogs/namedays/namedays_lt.csv",
            "Estonian": "cogs/namedays/namedays_ee.csv"
        }

        # Iterate over the files to find name days
        for country, file_path in files.items():
            with open(file_path, "r", encoding="utf-8") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=';')
                for row in csv_reader:
                    # Assuming the first column is the date and the second column is the names
                    date = row[0].strip()  # Remove any extra whitespace
                    names = row[1].strip()  # Remove any extra whitespace

                    # Check if the date matches today's date
                    if date == current_date:
                        if country == "Latvian":
                            names_lv = names
                        elif country == "Lithuanian":
                            names_lt = names
                        elif country == "Estonian":
                            names_ee = names
                        break  # Exit the loop since we found today's names

        # Create the response message
        response = ""
        if names_lv:
            response += f"**Latvian Name Days:** {names_lv}\n"
        if names_lt:
            response += f"**Lithuanian Name Days:** {names_lt}\n"
        if names_ee:
            response += f"**Estonian Name Days:** {names_ee}\n"

        # Send the message, or if no name days were found, inform the user
        if response:
            await interaction.response.send_message(response)
        else:
            await interaction.response.send_message("No name days today!")

async def setup(bot):
    await bot.add_cog(Namedays(bot))
