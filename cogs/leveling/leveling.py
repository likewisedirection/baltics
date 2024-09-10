import discord
from discord import app_commands
from discord.ext import commands
import mariadb
import math
import random
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

def generate_random_color():
    return discord.Colour(random.randint(0x000000, 0xFFFFFF))

class LevelSys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_cache = {}
        self.level_up_channel_id = int(os.getenv("LEVEL_UP_CHANNEL_ID"))

    @commands.Cog.listener()
    async def on_ready(self):
        print("Leveling system is online")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            guild_id = message.guild.id
            user_id = message.author.id

            cursor.execute("SELECT * FROM Users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            result = cursor.fetchone()

            if result is None:
                cur_level = 0
                xp = 0
                level_up_xp = 100
                cursor.execute("INSERT INTO Users (guild_id, user_id, level, xp, level_up_xp) VALUES (?, ?, ?, ?, ?)", 
                               (guild_id, user_id, cur_level, xp, level_up_xp))
                conn.commit()
            else:
                cur_level = result[2]
                xp = result[3]
                level_up_xp = result[4]

                xp += random.randint(1, 25)

                if xp >= level_up_xp:
                    new_level = cur_level + 1
                    new_level_up_xp = math.ceil(50 * new_level ** 2 + 100 * new_level + 50)

                    level_up_channel = self.bot.get_channel(self.level_up_channel_id)
                    if level_up_channel:
                        await level_up_channel.send(f"{message.author.mention} has leveled up to level {new_level}!")

                    await self.manage_roles(message.author, cur_level, new_level)

                    cursor.execute("UPDATE Users SET level = ?, xp = ?, level_up_xp = ? WHERE guild_id = ? AND user_id = ?", 
                                   (new_level, xp, new_level_up_xp, guild_id, user_id))
                else:
                    cursor.execute("UPDATE Users SET xp = ? WHERE guild_id = ? AND user_id = ?", 
                                   (xp, guild_id, user_id))

                conn.commit()

        except mariadb.Error as e:
            print(f"Error interacting with the database: {e}")

        finally:
            if conn:
                conn.close()

    async def manage_roles(self, member: discord.Member, old_level: int, new_level: int):
        role_name = f"Level {new_level}"
        prev_role_name = f"Level {old_level}"
        guild = member.guild

        if prev_role_name in self.role_cache:
            prev_role = self.role_cache[prev_role_name]
        else:
            prev_role = discord.utils.get(guild.roles, name=prev_role_name)
            if prev_role:
                self.role_cache[prev_role_name] = prev_role

        if prev_role:
            try:
                await member.remove_roles(prev_role)
            except discord.Forbidden:
                print("The bot does not have permission to remove roles.")
            except discord.HTTPException as e:
                print(f"An error occurred while removing the role: {e}")

        if role_name in self.role_cache:
            role = self.role_cache[role_name]
        else:
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                try:
                    role_color = generate_random_color()
                    role = await guild.create_role(name=role_name, color=role_color, reason="Creating role for leveling system")
                    self.role_cache[role_name] = role
                except discord.Forbidden:
                    print("The bot does not have permission to create roles.")
                except discord.HTTPException as e:
                    print(f"An error occurred while creating the role: {e}")

        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                print("The bot does not have permission to assign roles.")
            except discord.HTTPException as e:
                print(f"An error occurred while assigning the role: {e}")

    @app_commands.command(name="level", description="View the level card")
    async def level(self, interaction: discord.Interaction, member: discord.Member=None):
        if member is None:
            member = interaction.user

        guild_id = interaction.guild.id
        member_id = member.id

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM Users WHERE guild_id = ? AND user_id = ?", (guild_id, member_id))
            result = cursor.fetchone()

            if result is None:
                await interaction.response.send_message(f"{member.name} currently does not have a level.")
            else:
                level = result[2]
                xp = result[3]
                level_up_xp = result[4]
                await interaction.response.send_message(f"Level statistics for {member.name}: \nLevel: {level} \nXP: {xp} \nXP to Level Up: {level_up_xp}")

        except mariadb.Error as e:
            print(f"Error retrieving user level: {e}")

        finally:
            if conn:
                conn.close()

async def setup(bot):
    await bot.add_cog(LevelSys(bot))
