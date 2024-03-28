from modules.logger import Logger

from twitchio.ext import commands
from typing import Union

import aiosqlite
import dataclasses
import re


@dataclasses.dataclass
class Cmd:
    name: str
    description: str
    usage: str
    used: int
    cost: int
    status: bool
    aliases: list
    category: str
    dynamic: bool
    text: str


class CmdCog(commands.Cog):
    def __init__(self, connection: aiosqlite.Connection, bot) -> None:
        """
        Initializes a new cmd cog object.

        Parameters
        ----------
        connection : aiosqlite.Connection
            The connection to the database.
        command : Cmd
            The command object.
        logger : Logger
            The logger object.

        Returns
        -------
        None
        """

        self.bot = bot
        self.connection = connection
        self.command = None
        self.logger = Logger(__name__)

    async def __ainit__(self) -> None:
        """
        Initializes the cmd cog object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.command = await self._fill_default_table()

    async def create_table(self) -> None:
        """
        Creates the table.

        Returns
        -------
        None
        """

        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cmd (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                usage TEXT,
                used INTEGER,
                cost INTEGER,
                status INTEGER,
                aliases TEXT,
                category TEXT,
                dynamic INTEGER,
                text TEXT
            )
            """
        )
        await self.connection.commit()

    async def is_table_empty(self) -> bool:
        """
        Checks if the table is empty.

        Returns
        -------
        bool
            True if the table is empty, False otherwise.
        """

        async with self.connection.execute("SELECT * FROM cmd") as cursor:
            return not bool(await cursor.fetchone())

    async def _is_single_row_table(self) -> bool:
        """
        Checks if the table is configured.

        Returns
        -------
        bool
            True if the table is configured, False otherwise.
        """

        async with self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cmd'"
        ) as cursor:
            return bool(await cursor.fetchone())

    async def add_cmd(self, cmd: Union[Cmd, dict], standard=False) -> dict:
        """
        Adds a cmd.

        Returns
        -------
        dict
        """

        if isinstance(cmd, dict):
            cmd = Cmd(
                name=cmd["name"],
                description=cmd["description"],
                usage=0,
                used=0,
                cost=cmd["cost"],
                status=1,
                aliases="",
                category=cmd["category"],
                dynamic=1,
                text="",
            )

        if await self.is_cmd_exists(cmd.name):
            return {"error": "name already exists"}

        if not await self.is_name_valid(cmd.name):
            return {
                "error": f"command {cmd.name} must only contains letters or/and numbers"
            }

        if cmd.category == "Select category":
            return {"error": "category must be selected"}

        if str(cmd.cost).isdigit() is False:
            return {"error": "cost must be a number"}

        cmd.cost = int(cmd.cost)
        if cmd.cost < 0 or cmd.cost > 1000000000:
            return {"error": "cost must be between 0 and 1 000 000 000"}

        if cmd.description == "":
            return {"error": "description must not be empty"}

        await self.connection.execute(
            "INSERT INTO cmd (name, description, usage, used, cost, status, aliases, category, dynamic, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? , ?)",
            (
                cmd.name,
                cmd.description,
                cmd.usage,
                cmd.used,
                cmd.cost,
                cmd.status,
                cmd.aliases,
                cmd.category,
                cmd.dynamic,
                cmd.text,
            ),
        )
        await self.connection.commit()
        self.logger.info(f"Added cmd -> {cmd.name}.")

        if not standard:
            self.bot.add_command(commands.Command(cmd.name, self.bot.template_command))
        
        return {"success": f"command {cmd.name} added"}

    async def is_cmd_exists(self, name: str) -> bool:
        """
        Checks if the cmd exists.

        Parameters
        ----------
        name : str
            The cmd name.

        Returns
        -------
        bool
            True if the cmd exists, False otherwise.
        """

        async with self.connection.execute(
            "SELECT name FROM cmd WHERE name = ?", (name,)
        ) as cursor:
            return bool(await cursor.fetchone())

    async def increment_usage(self, name: str):
        """
        Increments the usage of a cmd.

        Parameters
        ----------
        name : str
            The cmd name.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "UPDATE cmd SET used = used + 1 WHERE name = ?", (name,)
        )
        await self.connection.commit()
        self.logger.debug(f"Incremented cmd usage -> {name}.")

    async def is_name_valid(self, name: str) -> bool:
        """
        Checks if the name is valid.

        Parameters
        ----------
        name : str
            The name.

        Returns
        -------
        bool
            True if the name is valid, it must contains only letters and numbers, False otherwise.
        """

        return bool(re.match("^[a-zA-Z0-9_]*$", name))

    async def get_cmd(self, name: str) -> Cmd:
        """
        Gets a cmd.

        Parameters
        ----------
        name : str
            The cmd name.

        Returns
        -------
        Cmd
            The cmd object.
        """

        self.logger.info(f"get_cmd -> {name}")

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE name = ?", (name,)
        ) as cursor:
            cmd = await cursor.fetchone()

        return Cmd(*cmd[1:])

    async def get_user_cmds(self) -> list[Cmd]:
        """
        Gets all dynamic cmds.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE dynamic = ?", (1,)
        ) as cursor:
            cmds = await cursor.fetchall()

        return [Cmd(*cmd[1:]) for cmd in cmds]

    async def get_all_cmds(self) -> list[Cmd]:
        """
        Gets all cmds.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute("SELECT * FROM cmd") as cursor:
            cmds = await cursor.fetchall()

        return [Cmd(*cmd[1:]) for cmd in cmds]

    async def update_status(self, name: str, status: bool) -> None:
        """
        Updates a cmd status.

        Parameters
        ----------
        name : str
            The cmd name.
        status : bool
            The cmd status.

        Returns
        -------
        None
        """

        # Convert the status to an integer
        status = 1 if status else 0

        await self.connection.execute(
            "UPDATE cmd SET status = ? WHERE name = ?", (status, name)
        )

        await self.connection.commit()
        self.logger.info(f"Updated cmd status -> {name} -> {status}.")

        # delete command
        if status == 0:
            await self.remove_command(name)

        if status == 1:
            await self.add_command(commands.Command(name, self.template_command))

        return {"success": f"command {name} status updated"}

    async def update_cmd(self, name: str, cmd: Union[Cmd, dict]) -> dict:
        """
        Updates a cmd.

        Parameters
        ----------
        name : str
            The cmd name.
        cmd : Cmd
            The cmd object.

        Returns
        -------
        None
        """

        if isinstance(cmd, dict):
            cmd = Cmd(
                name=cmd["name"],
                description=cmd["description"],
                usage=0,
                used=0,
                cost=cmd["cost"],
                status=1,
                aliases="",
                category=cmd["category"],
                dynamic=1,
                text="",
            )

        if cmd.category == "Select category":
            return {"error": "category must be selected"}

        if cmd.cost.isdigit() is False:
            return {"error": "cost must be a number"}

        cmd.cost = int(cmd.cost)
        if cmd.cost < 0 or cmd.cost > 1000000000:
            return {"error": "cost must be between 0 and 1 000 000 000"}

        if cmd.description == "":
            return {"error": "description must not be empty"}

        await self.connection.execute(
            "UPDATE cmd SET name = ?, description = ?, usage = ?, used = ?, cost = ?, status = ?, aliases = ?, category = ?, dynamic = ?, text = ? WHERE name = ?",
            (
                cmd.name,
                cmd.description,
                cmd.usage,
                cmd.used,
                cmd.cost,
                cmd.status,
                cmd.aliases,
                cmd.category,
                cmd.dynamic,
                cmd.text,
                name,
            ),
        )
        await self.connection.commit()
        self.logger.info(f"Updated cmd -> {cmd.name}.")
        return {"success": f"command {cmd.name} updated"}

    async def delete_cmd(self, name: str) -> None:
        """
        Deletes a cmd.

        Parameters
        ----------
        name : str
            The cmd name.

        Returns
        -------
        None
        """

        if isinstance(name, Cmd):
            name = name.name

        if isinstance(name, dict):
            name = name["name"]

        self.bot.remove_command(name)

        await self.connection.execute("DELETE FROM cmd WHERE name = ?", (name,))
        await self.connection.commit()
        self.logger.info(f"Deleted cmd -> {name}.")
        return {"success": f"command {name} deleted"}

    async def get_all_non_dynamic_cmds(self) -> list:
        """
        Gets all non dynamic cmds.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE dynamic = ?", (0,)
        ) as cursor:
            cmds = await cursor.fetchall()

        return [Cmd(*cmd[1:]) for cmd in cmds]

    async def get_all_dynamic_cmds(self) -> list:
        """
        Gets all dynamic cmds.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE dynamic = ?", (1,)
        ) as cursor:
            cmds = await cursor.fetchall()

        return [Cmd(*cmd[1:]) for cmd in cmds]

    @commands.command(name="about")
    async def about_bot(self, ctx: commands.Context):
        """
        About the bot.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        link = " discord.gg/xxqtuubayy"

        await self.increment_usage(ctx.command.name)
        await ctx.send(
            f"DoggoBot has been created by Fumi/Namsku - If you want more info ping him on his Discord ({link})"
        )

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """
        Pings the bot.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        await self.increment_usage(ctx.command.name)
        await ctx.send(f"Pong!")

    @commands.command(name="shoutout", aliases=["so"])
    async def shoutout(self, ctx: commands.Context) -> None:
        """
        Shoutouts a user.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 2:
            await ctx.send("Usage: !so <user>")
            return

        user = ctx.message.content.split()[1].lower().replace("@", "")
        game = await self.bot.usr.get_last_game(user)

        await self.increment_usage(ctx.command.name)

        await ctx.send(
            f" 📢 Please give a look to our >>> {user} <<< "
            f"Take a look at his twitch channel (twitch.tv/{str.lower(user)}) | Last stream was about {game}"
        )

    @commands.command(name="mods")
    async def info_mods(self, ctx: commands.Context):
        """
        Mods of the channel

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """
        await ctx.send(
            "📢 If you search a list of good mods/tools for RE, everything is on my discord (!socials for more info)"
        )

    @commands.command(name="schedule")
    async def schedule(self, ctx: commands.Context):
        """
        Schedule of the streamer

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        await self.increment_usage(ctx.command.name)
        await ctx.send("📢 The schedule is on the discord (!socials for more info)")

    @commands.command(name="help")
    async def help(self, ctx: commands.Context):
        """
        Help command

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        
        user = ctx.author.name.lower()

        if user not in self.bot.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        # give the full list of commands that are currently available from the bot
        bot_list = list(sorted([f"!{cmd}" for cmd in self.bot.commands.keys()]))

        await self.increment_usage(ctx.command.name)
        await ctx.send(f"📢 available commands: {' '.join(bot_list)}")

    @commands.command(name="sfx")
    async def sound_effects(self, ctx: commands.Context):
        """
        Sound effects command

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        
        user = ctx.author.name.lower()

        if user not in self.bot.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send("📢 The full list is on my discord (!socials for more info)")

    @commands.command(name="clip")
    async def clip(self, ctx: commands.Context) -> None:
        """
        Creates a clip.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        '''
            user = ctx.author.name.lower()

            if user not in self.bot.channel_members:
                await ctx.send(f"{user} is not following the channel.")
                return
        '''

        if len(ctx.message.content.split()) != 1:
                await ctx.send("Usage: !clip")
                return


        dict = await self.bot.user.create_clip(token=self.bot.token)
        ssss = await self.bot.fetch_clips(dict['id'])

        await self.increment_usage(ctx.command.name)
        self.logger.info(f"Clip created -> {dict} -> {ssss}")
        await ctx.send(f"📢 Clip created -> {dict['edit_url'].replace('/edit','')}")

    async def _fill_default_table(self) -> None:
        """
        Fills the table with default values.

        Returns
        -------
        None
        """

        # if table is not empty, quit
        if not await self.is_table_empty():
            return

        default_cmds = [
            ("about", "Information about the bot", "", 0, 0, 1, "", "bot", 0, None),
            (
                "balance",
                "Get the current balance of the user",
                "",
                0,
                0,
                1,
                "",
                "economy",
                0,
                None,
            ),
            (
                "clip",
                "Create a clip of the current streaming actions...",
                "",
                0,
                0,
                1,
                "",
                "stream",
                0,
                None,
            ),
            (
                "followage",
                "Get the timelapse since the user is following you",
                "",
                0,
                0,
                1,
                "",
                "stream",
                0,
                "",
            ),
            (
                "followdate",
                "Get the date where the user decided to follow you",
                "",
                0,
                0,
                1,
                "",
                "stream",
                0,
                None,
            ),
            (
                "gamble",
                "Gamble your coin with the bot",
                "",
                0,
                0,
                1,
                "",
                "games",
                0,
                None,
            ),
            (
                "gatcha",
                "Play a gatcha game with the bot",
                "",
                0,
                0,
                1,
                "",
                "games",
                0,
                None,
            ),
            (
                "help",
                "Get the current active commands that the user can execute",
                "",
                0,
                0,
                1,
                "",
                "bot",
                0,
                "",
            ),
            (
                "mods",
                "Get the mods that you are playing or you played",
                "",
                0,
                0,
                1,
                "",
                "games",
                0,
                None,
            ),
            ("ping", "Simple Ping/Pong request", "", 0, 0, 1, "", "bot", 0, None),
            (
                "schedule",
                "Get the current schedule of your stream",
                "",
                0,
                0,
                1,
                "",
                "stream",
                0,
                None,
            ),
            ("rpg", "Play a RPG game with the bot", "", 0, 0, 1, "", "games", 0, None),
            (
                "shoutout",
                "Give a shoutout to a specific user",
                "",
                0,
                0,
                1,
                "",
                "social",
                0,
                None,
            ),
            ("sfx", "Get the list of SFX commands", "", 0, 0, 1, "", "bot", 0, None),
            (
                "slots",
                "Play a slots game with the bot",
                "",
                0,
                0,
                1,
                "",
                "games",
                0,
                None,
            ),
            (
                "topchatter",
                "Get the top chatter of your stream",
                "",
                0,
                0,
                1,
                "",
                "bot",
                0,
                None,
            ),
            (
                "watchtime",
                "Since how many time are you streaming today",
                "",
                0,
                0,
                1,
                "",
                "stream",
                0,
                None,
            ),
        ]

        for entry in default_cmds:
            cmd = Cmd(*entry)
            await self.add_cmd(cmd, standard=True)

        self.logger.info("Filled default cmds.")

    def __str__(self) -> str:
        """
        Returns the string representation of the cmd object.

        Returns
        -------
        str
            The string representation of the cmd object.
        """

        return f"CmdCog -> {self.command}"
