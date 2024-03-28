from modules.logger import Logger

from twitchio import Message as TwitchMessage
from twitchio.ext import commands

import aiosqlite
import dataclasses


@dataclasses.dataclass
class Msg(commands.Cog):
    id: int
    author: str
    content: str
    timestamp: str
    channel: str
    is_bot: bool
    is_command: bool
    is_subscriber: bool
    is_vip: bool
    is_mod: bool
    is_turbo: bool


class MessageCog(commands.Cog):
    def __init__(self, connection: aiosqlite.Connection) -> None:
        """
        Initializes the message object.
        """
        self.connection = connection
        self.logger = Logger(__name__)
        self.message = None  # Msg

    async def set(self, message: TwitchMessage, bot) -> None:
        """
        Sets the message content.

        Parameters
        ----------
        message : TwitchMessage
            The message object.

        Returns
        -------
        None
        """

        # Automatically set the message object with the new ID
        self.message = Msg(
            id = await self.get_last_id() + 1,
            author=(
                message.author.name.lower() if message.author else bot.bot_name.lower()
            ),
            content=message.content,
            timestamp=message.timestamp,
            channel=message.channel.name,
            is_bot=await bot.usr.is_bot(
                message.author.name.lower() if message.author else bot.bot_name.lower()
            ),
            is_command=message.content.startswith("!"),
            is_subscriber=message.author.is_subscriber if message.author else False,
            is_vip=message.author.is_vip if message.author else False,
            is_mod=message.author.is_mod if message.author else False,
            is_turbo=message.author.is_turbo if message.author else False,
        )

    async def create_table(self) -> None:
        """
        Creates the message table.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                content TEXT,
                timestamp TEXT,
                channel TEXT,
                is_bot INTEGER,
                is_command INTEGER,
                is_subscriber INTEGER,
                is_vip INTEGER,
                is_mod INTEGER,
                is_turbo INTEGER
            )
            """
        )

    async def add_message(self, message: TwitchMessage, bot) -> None:
        """
        Adds a message to the database.

        Parameters
        ----------
        message : TwitchMessage
            The message object.

        Returns
        -------
        None
        """

        await self.set(message, bot)

        await self.connection.execute(
            """
            INSERT INTO message(
                author,
                content,
                timestamp,
                channel,
                is_bot,
                is_command,
                is_subscriber,
                is_vip,
                is_mod,
                is_turbo
            )
            VALUES (
                :author,
                :content,
                :timestamp,
                :channel,
                :is_bot,
                :is_command,
                :is_subscriber,
                :is_vip,
                :is_mod,
                :is_turbo
            )
            """,
            {
                "author": self.message.author,
                "content": self.message.content,
                "timestamp": self.message.timestamp,
                "channel": self.message.channel,
                "is_bot": self.message.is_bot,
                "is_command": self.message.is_command,
                "is_subscriber": self.message.is_subscriber,
                "is_vip": self.message.is_vip,
                "is_mod": self.message.is_mod,
                "is_turbo": self.message.is_turbo,
            },
        )

    async def get_last_id(self) -> int:
        """
        Returns the last message ID.

        Parameters
        ----------
        None

        Returns
        -------
        int
            The last message ID.
        """

        result = await self.connection.execute("SELECT MAX(id) FROM message")
        row = await result.fetchone()
        return row[0] if row[0] else 0


    def __str__(self) -> str:
        """
        Returns the string representation of the message object.
        """
