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
        print("leveling system is active")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        conn = None
        try:
            #fetch database entry
            conn = get_db_connection()
            cursor = conn.cursor()

            guild_id = message.guild.id
            user_id = message.author.id

            cursor.execute("SELECT level, xp, level_up_xp, level_up_ping FROM Users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            result = cursor.fetchone()

            if result is None:
                #if no entry, create new user entry
                cursor.execute("INSERT INTO Users (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
                conn.commit()
            else:
                #entry exists, fetch values
                cur_level, xp, level_up_xp, level_up_ping = result
                xp += random.randint(1, 25)

                if xp >= level_up_xp:
                    #qualifies for level up
                    new_level = cur_level + 1
                    new_level_up_xp = math.ceil(50 * new_level ** 2 + 100 * new_level + 50)

                    level_up_channel = self.bot.get_channel(self.level_up_channel_id)
                    if level_up_channel:
                        await level_up_channel.send(f"{message.author.mention} has leveled up to level {new_level}!", silent=not level_up_ping)

                    await self.manage_roles(message.author, cur_level, new_level)

                    cursor.execute("UPDATE Users SET level = ?, xp = ?, level_up_xp = ? WHERE guild_id = ? AND user_id = ?", 
                                   (new_level, xp, new_level_up_xp, guild_id, user_id))
                else:
                    #doesn't qualify for level up
                    cursor.execute("UPDATE Users SET xp = ? WHERE guild_id = ? AND user_id = ?", (xp, guild_id, user_id))

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

        #attempt to fetch role from cache, else add it to cache
        if prev_role_name in self.role_cache:
            prev_role = self.role_cache[prev_role_name]
        else:
            prev_role = discord.utils.get(guild.roles, name=prev_role_name)
            if prev_role:
                self.role_cache[prev_role_name] = prev_role

        #update level roles: remove current level role
        if prev_role:
            try:
                await member.remove_roles(prev_role)
            except discord.Forbidden:
                print("The bot does not have permission to remove roles.")
            except discord.HTTPException as e:
                print(f"An error occurred while removing the role: {e}")

        #attempt to fetch new role from cache, else create a new one (+add to cache)
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

        #update level roles: add new level role
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                print("The bot does not have permission to assign roles.")
            except discord.HTTPException as e:
                print(f"An error occurred while assigning the role: {e}")

    @app_commands.command(name="level", description="View the level card")
    async def level(self, interaction: discord.Interaction, member: discord.Member=None):
        #get info about fetcher
        if member is None:
            member = interaction.user

        guild_id = interaction.guild.id
        member_id = member.id

        conn = None
        try:
            #fetch database
            conn = get_db_connection()
            cursor = conn.cursor()

            #fetch values
            cursor.execute("SELECT * FROM Users WHERE guild_id = ? AND user_id = ?", (guild_id, member_id))
            result = cursor.fetchone()

            if result is None:
                #user does not have a level yet
                await interaction.response.send_message(f"{member.name} currently does not have a level.")
            else:
                #user does have a level
                level = result[2]
                xp = result[3]
                level_up_xp = result[4]
                await interaction.response.send_message(f"Level statistics for {member.name}: \nLevel: {level} \nXP: {xp} \nXP to Level Up: {level_up_xp}")

        except mariadb.Error as e:
            print(f"Error retrieving user level: {e}")

        finally:
            if conn:
                conn.close()

    @app_commands.command(name="togglelvlup", description="Toggle whether you receive a ping when you level up")
    async def togglepingonlevelup(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        conn = None
        try:
            #fetch database
            conn = get_db_connection()
            cursor = conn.cursor()

            #toggle level_up_ping
            cursor.execute(
                "UPDATE Users SET level_up_ping = NOT level_up_ping WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            conn.commit()

            cursor.execute(
                "SELECT level_up_ping FROM Users WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            result = cursor.fetchone()
            level_up_ping = result[0] if result else False

            await interaction.response.send_message(f"Ping on level up is now {'enabled' if level_up_ping else 'disabled'}", ephemeral=True)

        except mariadb.Error as e:
            print(f"Error toggling level up ping: {e}")
            await interaction.response.send_message(f"There was an error processing the request: {e}", ephemeral=True)

        finally:
            if conn:
                conn.close()

    @app_commands.command(name="lvlstats", description="View the top 10 users by level")
    async def lvlstats(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT user_id, level FROM Users WHERE guild_id = ? ORDER BY level DESC LIMIT 10",
                (guild_id,)
            )
            results = cursor.fetchall()

            top_users = [
                {"id": user_id, "level": level}
                for user_id, level in results
            ]

            embed = discord.Embed(title="Top 10 Levels", color=discord.Color.blue())
            embed.description = '\n'.join(
                [f"{i+1}. <@{user_data['id']}>: {user_data['level']} lvl" for i, user_data in enumerate(top_users)]
            )

            await interaction.response.send_message(embed=embed)

        except mariadb.Error as e:
            print(f"Error retrieving level stats: {e}")
            await interaction.response.send_message(f"There was an error processing the request: {e}", ephemeral=True)

        finally:
            if conn:
                conn.close()

async def setup(bot):
    await bot.add_cog(LevelSys(bot))
