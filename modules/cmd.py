from modules.logger import Logger

from dataclasses import dataclass
import aiosqlite


@dataclass
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


class CmdCog:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.connection = connection
        self.name = None
        self.description = None
        self.usage = None
        self.used = None
        self.cost = None
        self.status = None
        self.aliases = None
        self.category = None
        self.dynamic = None
        self.text = None
        self.logger = Logger(__name__)

    async def __ainit__(self) -> None:
        if not await self.is_table_configured():
            await self.fill_default_table()

    def __str__(self) -> str:
        """
        Returns the string representation of the cmd object.
        """

        return f"Cmd(name={self.name}, description={self.description}, usage={self.usage}, used={self.used}, cost={self.cost}, status={self.status}, aliases={self.aliases}, category={self.category})"

    def set(self, cmd: Cmd) -> None:
        """
        Sets the cmd content.

        Parameters
        ----------
        cmd : Cmd
            The cmd object.

        Returns
        -------
        None
        """

        self.name = cmd.name
        self.description = cmd.description
        self.usage = cmd.usage
        self.used = cmd.used
        self.cost = cmd.cost
        self.status = cmd.status
        self.aliases = cmd.aliases
        self.category = cmd.category

    async def fill_default_table(self) -> None:
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
            ("balance","Get the current balance of the user","",0,0,1,"","economy",0,None),
            ("clip","Create a clip of the current streaming actions...","",0,0,1,"","stream",0,None),
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
            (
                "sfx",
                "Get the list of SFX commands",
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
            await self.add_cmd(cmd)

        self.logger.info("Filled default cmds.")

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

    async def is_table_configured(self) -> bool:
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

    async def get_last_cmd(self) -> Cmd:
        """
        Gets the last cmd.

        Returns
        -------
        Cmd
            The cmd object.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd ORDER BY id DESC LIMIT 1"
        ) as cursor:
            cmd = await cursor.fetchone()

        return Cmd(cmd[1], cmd[2], cmd[3], cmd[4], cmd[5], cmd[6], cmd[7], cmd[8])

    async def add_cmd(self, cmd: Cmd) -> None:
        """
        Adds a cmd.

        Returns
        -------
        None
        """

        # Quit if the name already exists
        if await self.is_cmd_exists(cmd.name):
            return

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

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE name = ?", (name,)
        ) as cursor:
            cmd = await cursor.fetchone()

        return Cmd(
            cmd[1],
            cmd[2],
            cmd[3],
            cmd[4],
            cmd[5],
            cmd[6],
            cmd[7],
            cmd[8],
            cmd[9],
            cmd[10],
        )

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

        return [
            Cmd(
                cmd[1],
                cmd[2],
                cmd[3],
                cmd[4],
                cmd[5],
                cmd[6],
                cmd[7],
                cmd[8],
                cmd[9],
                cmd[10],
            )
            for cmd in cmds
        ]

    async def update_description(self, name: str, description: str) -> None:
        """
        Updates a cmd description.

        Parameters
        ----------
        name : str
            The cmd name.
        description : str
            The cmd description.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "UPDATE cmd SET description = ? WHERE name = ?", (description, name)
        )
        await self.connection.commit()

    async def update_aliases(self, name: str, aliases: list) -> None:
        """
        Updates a cmd aliases.

        Parameters
        ----------
        name : str
            The cmd name.
        aliases : list
            The cmd aliases.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "UPDATE cmd SET aliases = ? WHERE name = ?", (aliases, name)
        )
        await self.connection.commit()

    async def update_category(self, name: str, category: str) -> None:
        """
        Updates a cmd category.

        Parameters
        ----------
        name : str
            The cmd name.
        category : str
            The cmd category.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "UPDATE cmd SET category = ? WHERE name = ?", (category, name)
        )
        await self.connection.commit()

    async def update_cost(self, name: str, cost: int) -> None:
        """
        Updates a cmd cost.

        Parameters
        ----------
        name : str
            The cmd name.
        cost : int
            The cmd cost.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "UPDATE cmd SET cost = ? WHERE name = ?", (cost, name)
        )
        await self.connection.commit()

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

    async def update_cmd(self, name: str, cmd: Cmd) -> None:
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

        await self.connection.execute("DELETE FROM cmd WHERE name = ?", (name,))
        await self.connection.commit()

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

        return [
            Cmd(
                cmd[1],
                cmd[2],
                cmd[3],
                cmd[4],
                cmd[5],
                cmd[6],
                cmd[7],
                cmd[8],
                cmd[9],
                cmd[10],
            )
            for cmd in cmds
        ]

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

        return [
            Cmd(
                cmd[1],
                cmd[2],
                cmd[3],
                cmd[4],
                cmd[5],
                cmd[6],
                cmd[7],
                cmd[8],
                cmd[9],
                cmd[10],
            )
            for cmd in cmds
        ]

    async def get_cmd_by_alias(self, alias: str) -> Cmd:
        """
        Gets a cmd by alias.

        Parameters
        ----------
        alias : str
            The cmd alias.

        Returns
        -------
        Cmd
            The cmd object.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE aliases LIKE ?", (f"%{alias}%",)
        ) as cursor:
            cmd = await cursor.fetchone()

        return Cmd(
            cmd[1],
            cmd[2],
            cmd[3],
            cmd[4],
            cmd[5],
            cmd[6],
            cmd[7],
            cmd[8],
            cmd[9],
            cmd[10],
        )

    async def get_all_cmds_by_alias(self, alias: str) -> list:
        """
        Gets all cmds by alias.

        Parameters
        ----------
        alias : str
            The cmd alias.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE aliases LIKE ?", (f"%{alias}%",)
        ) as cursor:
            cmds = await cursor.fetchall()

        return [
            Cmd(
                cmd[1],
                cmd[2],
                cmd[3],
                cmd[4],
                cmd[5],
                cmd[6],
                cmd[7],
                cmd[8],
                cmd[9],
                cmd[10],
            )
            for cmd in cmds
        ]

    async def get_cmd_by_category(self, category: str) -> Cmd:
        """
        Gets a cmd by category.

        Parameters
        ----------
        category : str
            The cmd category.

        Returns
        -------
        Cmd
            The cmd object.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE category = ?", (category,)
        ) as cursor:
            cmd = await cursor.fetchone()

        return Cmd(
            cmd[1],
            cmd[2],
            cmd[3],
            cmd[4],
            cmd[5],
            cmd[6],
            cmd[7],
            cmd[8],
            cmd[9],
            cmd[10],
        )

    async def get_all_cmds_by_category(self, category: str) -> list:
        """
        Gets all cmds by category.

        Parameters
        ----------
        category : str
            The cmd category.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE category = ?", (category,)
        ) as cursor:
            cmds = await cursor.fetchall()

        return [
            Cmd(
                cmd[1],
                cmd[2],
                cmd[3],
                cmd[4],
                cmd[5],
                cmd[6],
                cmd[7],
                cmd[8],
                cmd[9],
                cmd[10],
            )
            for cmd in cmds
        ]

    async def get_cmd_by_status(self, status: bool) -> Cmd:
        """
        Gets a cmd by status.

        Parameters
        ----------
        status : bool
            The cmd status.

        Returns
        -------
        Cmd
            The cmd object.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE status = ?", (status,)
        ) as cursor:
            cmd = await cursor.fetchone()

        return Cmd(
            cmd[1],
            cmd[2],
            cmd[3],
            cmd[4],
            cmd[5],
            cmd[6],
            cmd[7],
            cmd[8],
            cmd[9],
            cmd[10],
        )

    async def get_all_cmds_by_status(self, status: bool) -> list:
        """
        Gets all cmds by status.

        Parameters
        ----------
        status : bool
            The cmd status.

        Returns
        -------
        list
            The cmds.
        """

        async with self.connection.execute(
            "SELECT * FROM cmd WHERE status = ?", (status,)
        ) as cursor:
            cmds = await cursor.fetchall()

        return [
            Cmd(
                cmd[1],
                cmd[2],
                cmd[3],
                cmd[4],
                cmd[5],
                cmd[6],
                cmd[7],
                cmd[8],
                cmd[9],
                cmd[10],
            )
            for cmd in cmds
        ]

    # convert Cmd to dict or list[dict]
    def to_dict(self, cmd: get_cmd) -> dict:
        """
        Converts the cmd object to a dict.

        Returns
        -------
        dict
            The cmd object as a dict.
        """

        return {
            "name": cmd.name,
            "description": cmd.description,
            "usage": cmd.usage,
            "used": cmd.used,
            "cost": cmd.cost,
            "status": cmd.status,
            "aliases": cmd.aliases,
            "category": cmd.category,
            "dynamic": cmd.dynamic,
            "text": cmd.text,
        }
