import discord
import yaml
import datetime
from discord.ext import commands
from discord import app_commands
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

with open("config.yml", "r") as file:
    data = yaml.safe_load(file)

guild_id = data["General"]["GUILD_ID"]
embed_color_value = data["General"].get("EMBED_COLOR", "#5865F2")
raw_roles = data.get("Permissions", {}).get("COMMAND_ROLES", []) or []
allowed_role_ids: List[int] = []
for role_id in raw_roles:
    try:
        allowed_role_ids.append(int(role_id))
    except (TypeError, ValueError):
        continue

CHECK_EMOJI = "✅"

def parse_color(raw: str):
    try:
        return discord.Color.from_str(raw)
    except Exception:
        try:
            return discord.Color(int(raw, 16))
        except Exception:
            return discord.Color.blurple()

def role_guard():
    async def predicate(interaction: discord.Interaction):
        if not allowed_role_ids:
            return True

        if not interaction.guild:
            raise app_commands.CheckFailure("This command can only be used in a server.")

        if any(role.id in allowed_role_ids for role in getattr(interaction.user, "roles", [])):
            return True

        raise app_commands.CheckFailure("You do not have the required role to run this command.")

    return app_commands.check(predicate)

@dataclass
class MiniSession:
    message_id: int
    channel_id: int
    created_by: int
    jump_url: str
    participants: Set[int] = field(default_factory=set)
    report_channel_id: Optional[int] = None
    monitor_unreactions: bool = False
    unreacted_after_retrieve: Set[int] = field(default_factory=set)
    last_retrieved_at: Optional[datetime.datetime] = None

@dataclass
class TeamState:
    color: str
    role_id: Optional[int]
    members: Set[int] = field(default_factory=set)

class GameConfigModal(discord.ui.Modal):
    def __init__(self, builder_view: "TeamBuilderView"):
        super().__init__(title="Set games & host")
        self.builder_view = builder_view

        self.game_one = discord.ui.TextInput(label="Game 1", placeholder="e.g., Splat Zones", required=False, max_length=60)
        self.game_two = discord.ui.TextInput(label="Game 2", placeholder="e.g., Tower Control", required=False, max_length=60)
        self.game_three = discord.ui.TextInput(label="Game 3", placeholder="e.g., Rainmaker", required=False, max_length=60)
        self.game_four = discord.ui.TextInput(label="Game 4", placeholder="e.g., Clam Blitz", required=False, max_length=60)
        self.host = discord.ui.TextInput(label="Plobby host", placeholder="Type a name", required=False, max_length=40)

        for item in (self.game_one, self.game_two, self.game_three, self.game_four, self.host):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        self.builder_view.games = [
            self.game_one.value or "TBD",
            self.game_two.value or "TBD",
            self.game_three.value or "TBD",
            self.game_four.value or "TBD",
        ]
        self.builder_view.host = self.host.value.strip() or "TBD"

        await interaction.response.edit_message(content=self.builder_view.build_preview(), view=self.builder_view)

class TeamSelect(discord.ui.UserSelect):
    def __init__(self, team_key: str, label: str, max_players: int):
        super().__init__(
            placeholder=f"Pick up to {max_players} players for {label}",
            min_values=0,
            max_values=max_players,
            custom_id=f"team_select_{team_key}",
        )
        self.team_key = team_key

    async def callback(self, interaction: discord.Interaction):
        view: TeamBuilderView = self.view
        if not await view.interaction_check(interaction):
            return

        selected_ids = {int(user_id) for user_id in interaction.data.get("values", [])}
        view.teams[self.team_key].members = selected_ids

        await interaction.response.edit_message(content=view.build_preview(), view=view)

class TeamBuilderView(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        owner_id: int,
        guild: discord.Guild,
        target_channel: discord.TextChannel,
        team_configs: Sequence[Tuple[str, Optional[discord.Role]]],
        max_players: int,
        embed_color: discord.Color,
    ):
        super().__init__(timeout=15 * 60)
        self.bot = bot
        self.owner_id = owner_id
        self.guild = guild
        self.target_channel = target_channel
        self.max_players = max_players
        self.embed_color = embed_color
        self.games: List[str] = ["TBD", "TBD", "TBD", "TBD"]
        self.host: str = "TBD"
        self.teams: Dict[str, TeamState] = {}
        self.message: Optional[discord.Message] = None

        for index, (color_name, role) in enumerate(team_configs, start=1):
            if not color_name:
                continue

            team_key = f"team_{index}"
            self.teams[team_key] = TeamState(color=color_name, role_id=role.id if role else None)
            self.add_item(TeamSelect(team_key=team_key, label=color_name, max_players=max_players))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Only the command user can change this view.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        self.disable_all_items()
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    def mention_member(self, member_id: int):
        member = self.guild.get_member(member_id)
        return member.mention if member else f"<@{member_id}>"

    def build_preview(self):
        lines: List[str] = ["Configure the mini layout before posting.", f"Target channel: {self.target_channel.mention}", ""]

        lines.append("**Teams**")
        for team in self.teams.values():
            member_mentions = ", ".join(self.mention_member(member_id) for member_id in team.members) if team.members else "No players yet."
            role_text = ""
            if team.role_id:
                role_obj = self.guild.get_role(team.role_id)
                if role_obj:
                    role_text = f" (role: {role_obj.mention})"
            lines.append(f"- {team.color}{role_text}: {member_mentions}")

        lines.append("")
        lines.append("**Game order**")
        for index, game in enumerate(self.games, start=1):
            lines.append(f"{index}. {game}")

        lines.append(f"\n**Plobby host**: {self.host}")

        return "\n".join(lines)

    def build_embed(self):
        embed = discord.Embed(title="Mini announcement", color=self.embed_color)
        embed.add_field(name="Teams", value=self._build_team_block(), inline=False)
        embed.add_field(name="Game order", value=self._build_game_block(), inline=False)
        embed.add_field(name="Plobby host", value=self.host, inline=False)
        embed.set_footer(text="Make sure to add the ✅ on the main post to join the mini.")
        return embed

    def _build_team_block(self):
        lines: List[str] = []
        for team in self.teams.values():
            member_mentions = ", ".join(self.mention_member(member_id) for member_id in team.members) if team.members else "Waiting for picks"
            lines.append(f"{team.color}: {member_mentions}")
        return "\n".join(lines) if lines else "No teams configured."

    def _build_game_block(self):
        lines = [f"{index}. {game}" for index, game in enumerate(self.games, start=1)]
        return "\n".join(lines)

    async def apply_roles(self):
        issues: List[str] = []

        for team in self.teams.values():
            if not team.role_id or not team.members:
                continue

            role_obj = self.guild.get_role(team.role_id)
            if not role_obj:
                issues.append(f"Missing role for {team.color}.")
                continue

            for member_id in team.members:
                member = self.guild.get_member(member_id)
                if not member:
                    issues.append(f"Could not find member {member_id} for {team.color}.")
                    continue
                if role_obj in member.roles:
                    continue
                try:
                    await member.add_roles(role_obj, reason="Mini team assignment")
                except discord.Forbidden:
                    issues.append(f"Missing permission to give {role_obj.name} to {member.display_name}.")
                except discord.HTTPException:
                    issues.append(f"Failed to give {role_obj.name} to {member.display_name}.")

        return issues

    @discord.ui.button(label="Set games & host", style=discord.ButtonStyle.primary)
    async def set_games(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.send_modal(GameConfigModal(self))

    @discord.ui.button(label="Post summary", style=discord.ButtonStyle.success)
    async def post_summary(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        embed = self.build_embed()
        posted_message = await self.target_channel.send(embed=embed)
        issues = await self.apply_roles()

        response_lines = [
            f"Posted to {self.target_channel.mention}: {posted_message.jump_url}",
        ]

        if issues:
            response_lines.append("Role notes:")
            response_lines.extend(f"- {issue}" for issue in issues)

        await interaction.followup.send("\n".join(response_lines), ephemeral=True)

        self.disable_all_items()
        if self.message:
            try:
                await self.message.edit(content="Summary posted.", view=self)
            except discord.HTTPException:
                pass
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return

        await interaction.response.send_message("Cancelled.", ephemeral=True)
        self.disable_all_items()
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass
        self.stop()

class MiniCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions: Dict[int, MiniSession] = {}
        self.embed_color = parse_color(embed_color_value)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send(str(error), ephemeral=True)
            else:
                await interaction.response.send_message(str(error), ephemeral=True)
            return
        raise error

    @app_commands.command(name="mini", description="Post a mini announcement and track reactions.")
    @role_guard()
    @app_commands.describe(
        start_in_minutes="Minutes from now until the mini starts (auto time-zone friendly).",
        channel="Channel to post the announcement in.",
        mention_role="Role to ping (defaults to a plain @mini).",
        notes="Optional extra text for the announcement.",
    )
    async def mini(self, interaction: discord.Interaction, start_in_minutes: app_commands.Range[int, 5, 10080] = 30, channel: Optional[discord.TextChannel] = None, mention_role: Optional[discord.Role] = None, notes: Optional[str] = None):
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message("Pick a text channel for the mini announcement.", ephemeral=True)
            return

        start_at = discord.utils.utcnow() + datetime.timedelta(minutes=start_in_minutes)
        time_display = f"{discord.utils.format_dt(start_at, style='F')} ({discord.utils.format_dt(start_at, style='R')})"

        mention_text = mention_role.mention if mention_role else "@mini"
        content = f"{mention_text} react below to play in the mini."

        embed = discord.Embed(title="Mini announcement", color=self.embed_color)
        embed.add_field(name="Start time", value=time_display, inline=False)
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)
        embed.set_footer(text="Add a ✅ reaction to join. Use /retrieve to get the player list.")

        message = await target_channel.send(content=content, embed=embed)
        try:
            await message.add_reaction(CHECK_EMOJI)
        except discord.HTTPException:
            pass

        self.sessions[message.id] = MiniSession(
            message_id=message.id,
            channel_id=target_channel.id,
            created_by=interaction.user.id,
            jump_url=message.jump_url,
        )

        await interaction.response.send_message(f"Mini posted in {target_channel.mention}. Link: {message.jump_url}", ephemeral=True)

    @app_commands.command(name="retrieve", description="Send the list of players who reacted to a mini message.")
    @role_guard()
    @app_commands.describe(
        announcement_channel="Channel where the mini announcement lives.",
        message_id="ID of the mini announcement message.",
        target_channel="Channel to send the player list to.",
        title="Heading text for the report.",
    )
    async def retrieve(self, interaction: discord.Interaction, announcement_channel: discord.TextChannel, message_id: str, target_channel: discord.TextChannel, title: str = "Who reacted"):
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.followup.send("Message ID must be a number.", ephemeral=True)
            return

        try:
            message = await announcement_channel.fetch_message(message_id_int)
        except discord.NotFound:
            await interaction.followup.send("I could not find that message.", ephemeral=True)
            return

        check_reaction = next((reaction for reaction in message.reactions if str(reaction.emoji) == CHECK_EMOJI), None)
        if not check_reaction:
            await interaction.followup.send("That message does not have the ✅ reaction to track.", ephemeral=True)
            return

        users: List[discord.abc.User] = []
        async for user in check_reaction.users():
            if user.bot:
                continue
            users.append(user)

        participant_ids = {user.id for user in users}

        session = self.sessions.get(message.id)
        if not session:
            session = MiniSession(
                message_id=message.id,
                channel_id=announcement_channel.id,
                created_by=interaction.user.id,
                jump_url=message.jump_url,
            )
            self.sessions[message.id] = session

        session.participants = participant_ids
        session.monitor_unreactions = True
        session.report_channel_id = target_channel.id
        session.last_retrieved_at = discord.utils.utcnow()
        session.unreacted_after_retrieve.clear()

        player_list = "\n".join(user.mention for user in users) if users else "No reactions yet."
        embed = discord.Embed(title=title, description=f"[Mini message]({message.jump_url})", color=self.embed_color)
        embed.add_field(name=f"Players ({len(users)})", value=player_list, inline=False)
        embed.set_footer(text="Unreacts after this will be posted here.")

        await target_channel.send(embed=embed)
        await interaction.followup.send(f"Sent the player list to {target_channel.mention}. I'll log unreacts there.", ephemeral=True)

    @app_commands.command(name="teams", description="Build a mini layout with teams, game order, host, and optional role assignments.")
    @role_guard()
    @app_commands.describe(
        target_channel="Channel to post the final layout into.",
        team_one_color="Team color/name for the first team.",
        team_two_color="Team color/name for the second team.",
        team_three_color="Optional color/name for a third team.",
        team_one_role="Role to give to team one players (optional).",
        team_two_role="Role to give to team two players (optional).",
        team_three_role="Role to give to team three players (optional).",
        max_players="Max players per team (up to 5).",
    )
    async def teams(self, interaction: discord.Interaction, target_channel: discord.TextChannel, team_one_color: str, team_two_color: str, team_three_color: Optional[str] = None, team_one_role: Optional[discord.Role] = None, team_two_role: Optional[discord.Role] = None, team_three_role: Optional[discord.Role] = None, max_players: app_commands.Range[int, 1, 5] = 5):
        if not interaction.guild:
            await interaction.response.send_message("Run this inside a server to build teams.", ephemeral=True)
            return

        team_one_color = team_one_color.strip()
        team_two_color = team_two_color.strip()
        team_three_color = (team_three_color or "").strip() or None

        if not team_one_color or not team_two_color:
            await interaction.response.send_message("Please provide names/colors for at least two teams.", ephemeral=True)
            return

        view = TeamBuilderView(
            bot=self.bot,
            owner_id=interaction.user.id,
            guild=interaction.guild,
            target_channel=target_channel,
            team_configs=[
                (team_one_color, team_one_role),
                (team_two_color, team_two_role),
                (team_three_color or "", team_three_role),
            ],
            max_players=max_players,
            embed_color=self.embed_color,
        )

        preview = view.build_preview()
        await interaction.response.send_message(preview, view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.sessions:
            return
        if str(payload.emoji) != CHECK_EMOJI:
            return
        if payload.user_id == self.bot.user.id:
            return

        session = self.sessions[payload.message_id]
        session.participants.add(payload.user_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.sessions:
            return
        if str(payload.emoji) != CHECK_EMOJI:
            return
        if payload.user_id == self.bot.user.id:
            return

        session = self.sessions[payload.message_id]
        session.participants.discard(payload.user_id)

        if session.monitor_unreactions:
            if payload.user_id in session.unreacted_after_retrieve:
                return

            session.unreacted_after_retrieve.add(payload.user_id)

            report_channel = self.bot.get_channel(session.report_channel_id) if session.report_channel_id else None
            if not report_channel or not isinstance(report_channel, discord.TextChannel):
                return

            user = self.bot.get_user(payload.user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(payload.user_id)
                except discord.HTTPException:
                    user = None

            try:
                await report_channel.send(f"{user.mention if user else f'User {payload.user_id}'} removed their ✅ from the mini: {session.jump_url}")
            except (discord.Forbidden, discord.HTTPException):
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(MiniCog(bot), guilds=[discord.Object(id=guild_id)])
