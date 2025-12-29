import discord
import asyncio
import aiosqlite
import datetime
import yaml
import sys
from discord.ext.commands import CommandNotFound, BadArgument
from discord import app_commands
from discord.ext import commands

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

guild_id = data["General"]["GUILD_ID"]
embed_color = data["General"]["EMBED_COLOR"]
activity = data["General"]["ACTIVITY"].lower()
doing_activity = data["General"]["DOING_ACTIVITY"]
streaming_activity_twitch_url = data["General"]["STREAMING_ACTIVITY_TWITCH_URL"]
status = data["General"]["STATUS"].lower()
token = data["General"]["TOKEN"]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if status == "online":
    _status = getattr(discord.Status, status)
elif status == "idle":
    _status = getattr(discord.Status, status)
elif status == "dnd":
    _status = getattr(discord.Status, status)
elif status == "invisible":
    _status = getattr(discord.Status, status)
else:
    sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Status: {bcolors.ENDC}{bcolors.OKCYAN}{status}{bcolors.ENDC}
{bcolors.OKBLUE}Valid Options: {bcolors.ENDC}{bcolors.OKGREEN}{bcolors.UNDERLINE}online{bcolors.ENDC}{bcolors.OKGREEN}, {bcolors.UNDERLINE}idle{bcolors.ENDC}{bcolors.OKGREEN}, {bcolors.UNDERLINE}dnd{bcolors.ENDC}{bcolors.OKGREEN}, or {bcolors.UNDERLINE}invisible{bcolors.ENDC}
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 7
""")

if activity == "playing":
    if doing_activity == "":
        sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Doing Activity: {bcolors.OKBLUE}It Must Be Set!
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 5
""")
    else:
        _activity = discord.Game(name=doing_activity)
elif activity == "watching":
    if doing_activity == "":
        sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Doing Activity: {bcolors.OKBLUE}It Must Be Set!
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 5
""")
    else:
        _activity = discord.Activity(name=doing_activity, type=discord.ActivityType.watching)
elif activity == "listening":
    if doing_activity == "":
        sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Doing Activity: {bcolors.OKBLUE}It Must Be Set!
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 5
""")
    else:
        _activity = discord.Activity(name=doing_activity, type=discord.ActivityType.listening)
elif activity == "streaming":
    if streaming_activity_twitch_url == "":
        sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Streaming Activity Twitch URL: {bcolors.OKBLUE}It Must Be Set!
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 6
""")
    elif not "https://twitch.tv/" in streaming_activity_twitch_url:
        sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Streaming Activity Twitch URL: {bcolors.OKBLUE}It Must Be A Valid Twitch URL!
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 6
""")
    else:
        _activity = discord.Streaming(name=doing_activity, url=streaming_activity_twitch_url)
else:
    sys.exit(f"""
{bcolors.FAIL}{bcolors.BOLD}ERROR:{bcolors.ENDC}
{bcolors.FAIL}Invalid Activity: {bcolors.ENDC}{bcolors.OKCYAN}{activity}{bcolors.ENDC}
{bcolors.OKBLUE}Valid Options: {bcolors.ENDC}{bcolors.OKGREEN}{bcolors.UNDERLINE}playing{bcolors.ENDC}{bcolors.OKGREEN}, {bcolors.UNDERLINE}watching{bcolors.ENDC}{bcolors.OKGREEN}, {bcolors.UNDERLINE}listening{bcolors.ENDC}{bcolors.OKGREEN}, or {bcolors.UNDERLINE}streaming{bcolors.ENDC}
{bcolors.OKGREEN}config.json {bcolors.OKCYAN}Line 4
""")

intents = discord.Intents.all()

initial_extensions = [
                      'cogs.commands.helpers.helpers',
                      'cogs.commands.moderation.ban',
                      'cogs.commands.moderation.dm',
                      'cogs.commands.moderation.forceban',
                      'cogs.commands.moderation.history',
                      'cogs.commands.moderation.kick',
                      'cogs.commands.moderation.misc',
                      'cogs.commands.moderation.mute',
                      'cogs.commands.moderation.temprole',
                      'cogs.commands.moderation.verify',
                      'cogs.commands.moderation.warn',
                      'cogs.commands.panels.panels',
                      'cogs.commands.tickets.tickets',
                      'cogs.commands.utils.command',
                      'cogs.commands.utils.help',
                      'cogs.commands.utils.misc',
                      'cogs.commands.utils.remindme',
                      'cogs.commands.utils.suggest',
                      'cogs.events.channelevents',
                      'cogs.events.memberevents',
                      'cogs.events.messageevents',
                      'cogs.events.roleevents',
                      'cogs.events.voiceevents',
                      'cogs.functions.api.api'
                      ]

class CamillaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('.'), owner_id=503641822141349888, intents=intents, activity=_activity, status=_status)
        self.persistent_views_added = False

    async def on_ready(self):

        print(f'Signed in as {self.user}')

        print('Attempting to sync commands...')
        await self.tree.sync()
        await self.tree.sync(guild=discord.Object(id=guild_id))
        print('Succesfully synced slash commands!')

    async def setup_hook(self):

        await client.load_extension('jishaku')
        for extension in initial_extensions:
            await self.load_extension(extension)

client = CamillaBot()
client.remove_command('help')
client.launch_time = datetime.datetime.now(datetime.UTC)
client.commandNames = []

@client.command()
async def sa(ctx: commands.Context):
    await ctx.reply(ctx.guild.icon.url)

@client.command()
@commands.is_owner()
async def sqlite(ctx):
    async with aiosqlite.connect('database.db') as db:
        await db.execute("""
        CREATE TABLE transcripts (
            user_id INTEGER,
            creator_name STRING,
            channel_name STRING,
            created STRING,
            transcript_id INTEGER,
            transcript STRING
        )""")
        await db.commit()
        a = await ctx.reply('Done!')
        await asyncio.sleep(5)
        await a.delete()
        await ctx.message.delete()

@client.command()
@commands.is_owner()
async def delete(ctx):
    async with aiosqlite.connect('database.db') as db:
        await db.execute('DROP TABLE transcripts;')
        await db.commit()
        a = await ctx.reply('Done!')
        await asyncio.sleep(5)
        await ctx.message.delete()
        await a.delete()

@client.command()
@commands.is_owner()
async def sqlite2(ctx):
    async with aiosqlite.connect('database.db') as db:
        await db.execute('DROP TABLE counter;')
        await db.execute("""
        CREATE TABLE counter (
            ticket INTEGER,
            suggestions INTEGER
        )""")
        await db.commit()
        await db.execute('INSERT INTO counter VALUES (?,?);', (0, 626))
        await db.commit()
        a = await ctx.reply('Done!')
        await asyncio.sleep(5)
        await a.delete()
        await ctx.message.delete()

@client.tree.context_menu(name='Report Message', guild=discord.Object(id=guild_id))
@app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.guild_id, i.user.id))
async def reportmessage(interaction: discord.Interaction, message: discord.Message):
    if message.author == interaction.user:
        await interaction.response.send_message("You can't report your own message, silly!", ephemeral=True)
    elif message.author.bot:
        await interaction.response.send_message("You can't report a bot's message, silly!", ephemeral=True)
    else:
        channel = client.get_channel(1023788161572274246)
        await interaction.response.send_message(f"This message has been sent the the Moderation Team to review.", ephemeral=True)
        embed = discord.Embed(title=f"Reported Message", description=f"{message.content}", color=discord.Color.from_str(embed_color))
        embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
        embed.timestamp = datetime.datetime.now()
        await channel.send(content=f"Message reported by {interaction.user.mention} ({interaction.user.id}). \n \n{message.jump_url}", embed=embed)
        if len(message.attachments) > 0:
            for m in message.attachments:
                await channel.send(f"{m.url}")

class ReportUser(discord.ui.Modal, title='Report User'):
    def __init__(self, member):
        super().__init__()
        self.member = member

    reason = discord.ui.TextInput(
        label=f"Why are you reporting this user?",
        style=discord.TextStyle.long,
        placeholder='Type your reason here...',
        required=True,
        max_length=4000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = client.get_channel(1023788161572274246)
        await interaction.response.send_message(f"Thank you for your report! {self.member.mention} will be investigated.", ephemeral=True)
        em = discord.Embed(title=f"Reported User", description=f"{self.member.mention} ({self.member.id}) \n \n**Reason**: {self.reason.value}", color=discord.Color.from_str(embed_color))
        em.set_author(name=self.member, icon_url=self.member.display_avatar.url)
        em.timestamp = datetime.datetime.now()
        await channel.send(content=f"User reported by {interaction.user.mention} ({interaction.user.id}).", embed=em)

@client.tree.context_menu(name='Report User', guild=discord.Object(id=guild_id))
@app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.guild_id, i.user.id))
async def reportuser(interaction: discord.Interaction, member: discord.Member):
    if member == interaction.user:
        await interaction.response.send_message("You can't report yourself, silly!", ephemeral=True)
    elif member.bot:
        await interaction.response.send_message("You can't report a bot, silly!", ephemeral=True)
    else:
        await interaction.response.send_modal(ReportUser(member))

#\\\\\\\\\\\\Error Handler////////////
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    if isinstance(error, BadArgument):
        a = await ctx.reply('Invalid usage!')
        await asyncio.sleep(5)
        await a.delete()
        await ctx.message.delete()
        return
    if isinstance(error, commands.NotOwner):
        await ctx.message.add_reaction('‼️')
        a = await ctx.reply('You may not use this command!')
        await asyncio.sleep(3)
        await a.delete()
        await ctx.message.delete()
        return
    raise error

@client.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        time  = round(error.retry_after, 2)
        await interaction.response.send_message(f"You can only report a message every 30 seconds! You can report the next message in {time}s.", ephemeral=True)
        return
    raise error

client.run(token)