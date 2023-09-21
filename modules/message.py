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
    is_broadcaster: bool
    is_owner: bool
    is_admin: bool
    is_global_mod: bool
    is_staff: bool
    is_turbo: bool
    is_prime: bool
    is_sub: bool
    is_founder: bool


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
        self.is_broadcaster = None
        self.is_owner = None
        self.is_admin = None
        self.is_global_mod = None
        self.is_staff = None
        self.is_turbo = None
        self.is_prime = None
        self.is_sub = None
        self.is_founder = None

        self.connection = connection

    def __str__(self) -> str:
        """
        Returns the string representation of the message object.
        """

        return f"Message(author={self.author}, content={self.content}, timestamp={self.timestamp}, channel={self.channel}, is_bot={self.is_bot}, is_command={self.is_command}, is_subscriber={self.is_subscriber}, is_vip={self.is_vip}, is_mod={self.is_mod}, is_broadcaster={self.is_broadcaster}, is_owner={self.is_owner}, is_admin={self.is_admin}, is_global_mod={self.is_global_mod}, is_staff={self.is_staff}, is_turbo={self.is_turbo}, is_prime={self.is_prime}, is_sub={self.is_sub}, is_founder={self.is_founder})"

    def set(self, message: TwitchMessage) -> None:
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
            message.author.name.lower() if message.author else self.bot_name.lower()
        )
        self.content = message.content
        self.timestamp = message.timestamp
        self.channel = message.channel
        self.is_bot = message.author.is_bot()
        self.is_command = message.author.is_command()
        self.is_subscriber = message.author.is_subscriber()
        self.is_vip = message.author.is_vip()
        self.is_mod = message.author.is_mod()
        self.is_broadcaster = message.author.is_broadcaster()
        self.is_owner = message.author.is_owner()
        self.is_admin = message.author.is_admin()
        self.is_global_mod = message.author.is_global_mod()
        self.is_staff = message.author.is_staff()
        self.is_turbo = message.author.is_turbo()
        self.is_prime = message.author.is_prime()
        self.is_sub = message.author.is_sub()
        self.is_founder = message.author.is_founder()

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
        self.is_broadcaster = message["is_broadcaster"]
        self.is_owner = message["is_owner"]
        self.is_admin = message["is_admin"]
        self.is_global_mod = message["is_global_mod"]
        self.is_staff = message["is_staff"]
        self.is_turbo = message["is_turbo"]
        self.is_prime = message["is_prime"]
        self.is_sub = message["is_sub"]
        self.is_founder = message["is_founder"]

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
                is_broadcaster INTEGER,
                is_owner INTEGER,
                is_admin INTEGER,
                is_global_mod INTEGER,
                is_staff INTEGER,
                is_turbo INTEGER,
                is_prime INTEGER,
                is_sub INTEGER,
                is_founder INTEGER
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

        self.set(message)

        self.connection.execute(
            """
            INSERT INTO message
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
                :is_broadcaster,
                :is_owner,
                :is_admin,
                :is_global_mod,
                :is_staff,
                :is_turbo,
                :is_prime,
                :is_sub,
                :is_founder
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
                "is_broadcaster": self.is_broadcaster,
                "is_owner": self.is_owner,
                "is_admin": self.is_admin,
                "is_global_mod": self.is_global_mod,
                "is_staff": self.is_staff,
                "is_turbo": self.is_turbo,
                "is_prime": self.is_prime,
                "is_sub": self.is_sub,
                "is_founder": self.is_founder,
            },
        )
