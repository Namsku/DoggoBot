from modules.logger import Logger

from twitchio import Message as TwitchMessage

import aiosqlite
import dataclasses


@dataclasses.dataclass
class Msg:
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


class MessageCog:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        """
        Initializes the message object.
        """
        self.connection = connection
        self.logger = Logger(__name__)
        self.message = Msg()

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

        self.message = Msg(
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

    async def add_message(self, message: TwitchMessage) -> None:
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

        await self.set(message)

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
                "author": self.author,
                "content": self.content,
                "timestamp": self.timestamp,
                "channel": self.channel,
                "is_bot": self.is_bot,
                "is_command": self.is_command,
                "is_subscriber": self.is_subscriber,
                "is_vip": self.is_vip,
                "is_mod": self.is_mod,
                "is_turbo": self.is_turbo,
            },
        )

    def __str__(self) -> str:
        """
        Returns the string representation of the message object.
        """
