from twitchio import Message as TwitchMessage
from dataclasses import dataclass

import aiosqlite


@dataclass
class Message:
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

        self.author = None
        self.content = None
        self.timestamp = None
        self.channel = None
        self.is_bot = None
        self.is_command = None
        self.is_subscriber = None
        self.is_vip = None
        self.is_mod = None
        self.is_turbo = None

        self.connection = connection

    def __str__(self) -> str:
        """
        Returns the string representation of the message object.
        """

        return f"Message(author={self.author}, content={self.content}, timestamp={self.timestamp}, channel={self.channel}, is_bot={self.is_bot}, is_command={self.is_command}, is_subscriber={self.is_subscriber}, is_vip={self.is_vip}, is_mod={self.is_mod}, is_turbo={self.is_turbo})"

    async def set(self, message: Message, bot) -> None:
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

        self.author = (
            message.author.name.lower() if message.author else bot.bot_name.lower()
        )

        self.content = message.content
        self.timestamp = message.timestamp
        self.channel = message.channel.name
        self.is_bot = await bot.usr.is_bot(self.author)
        self.is_command = True if message.content.startswith("!") else False
        self.is_subscriber = True if message.author.is_subscriber else False
        self.is_vip = message.author.is_vip
        self.is_mod = message.author.is_mod
        self.is_turbo = message.author.is_turbo

    async def set_message(self, message: dict) -> None:
        """
        Sets the message content.

        Parameters
        ----------
        message : dict
            The message dict.

        Returns
        -------
        None
        """

        self.author = message["author"]
        self.content = message["content"]
        self.timestamp = message["timestamp"]
        self.channel = message["channel"]
        self.is_bot = message["is_bot"]
        self.is_command = message["is_command"]
        self.is_subscriber = message["is_subscriber"]
        self.is_vip = message["is_vip"]
        self.is_mod = message["is_mod"]
        self.is_turbo = message["is_turbo"]

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
