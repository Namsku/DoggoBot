import aiosqlite
import os
from dataclasses import dataclass

from modules.logger import Logger

logger = Logger(__name__)


@dataclass
class Channel:
    id: int
    bot_name: str
    streamer_channel: str
    prefix: str
    coin_name: str
    income: int
    timeout: int


class ChannelCog:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def __ainit__(self) -> None:
        if not await self.is_table_configured():
            channel = self.get_default_config()
        else:
            channel = await self.get_last_channel()

        self.id = channel.id
        self.bot_name = channel.bot_name
        self.streamer_channel = channel.streamer_channel
        self.prefix = channel.prefix
        self.coin_name = channel.coin_name
        self.income = channel.income
        self.timeout = channel.timeout

        if not await self.is_table_configured():
            await self.add_channel()

    def __str__(self) -> str:
        """
        Returns the string representation of the channel object.
        """

        return f"Channel(bot_name={self.bot_name}, streamer_channel={self.streamer_channel}, prefix={self.prefix}, coin_name={self.coin_name}, income={self.income}, timeout={self.timeout})"

    def set(self, channel: Channel) -> None:
        """
        Sets the channel content.

        Parameters
        ----------
        channel : Channel
            The channel object.

        Returns
        -------
        None
        """

        self.id = channel.id
        self.bot_name = channel.bot_name
        self.streamer_channel = channel.streamer_channel
        self.prefix = channel.prefix
        self.coin_name = channel.coin_name
        self.income = channel.income
        self.timeout = channel.timeout

    async def set_channel(self, config: dict) -> None:
        """
        Sets the channel content.

        Parameters
        ----------
        config : dict
            The channel config.

        Returns
        -------
        None
        """

        print(config)

        self.bot_name = config["bot_name"]
        self.streamer_channel = config["streamer_channel"]
        self.prefix = config["prefix"]
        self.coin_name = config["coin_name"]
        self.income = config["default_income"]
        self.timeout = config["default_timeout"]

        await self.update_channel()

    def set_env(self, config: dict) -> None:
        """
        Sets the environment variables.

        Parameters
        ----------
        config : dict
            The environment variables.

        Returns
        -------
        None
        """

        try:
            # file is created at the root of the project
            with open(".env", "w") as file:
                file.write(f"TWITCH_SECRET_TOKEN={config['secret_token']}\n")
                file.write(f"TWITCH_CLIENT_TOKEN={config['client_token']}\n")
        except Exception as e:
            logger.error(f"Error while writing the .env file: {e}")
            exit(1)

        logger.debug("Environment variables updated successfully.")

    def get_default_config(self) -> Channel:
        """
        Gets the default config values.

        Parameters
        ----------
        None

        Returns
        -------
        config : Channel
            The default config values.
        """

        return Channel(
            1,
            "your_amazing_bot_name",
            "your_amazing_streamer_channel_name",
            "!",
            "DoggoCoin(s)",
            10000,
            5,
        )

    async def create_table(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS channel (
                id INTEGER PRIMARY KEY,
                bot_name TEXT,
                streamer_channel TEXT,
                prefix TEXT,
                coin_name TEXT,
                income INTEGER,
                timeout INTEGER
            )
        """
        )

        await self.connection.commit()

    async def is_table_configured(self) -> bool:
        """
        Checks if the table is having one row.

        Parameters
        ----------
        None

        Returns
        -------
        bool
            True if the table is having one row, False otherwise.
        """

        async with self.connection.execute(
            """
            SELECT COUNT(*) FROM channel
        """
        ) as cursor:
            result = await cursor.fetchone()

        if result[0] == 1:
            return True

        return False

    async def update_channel(self):
        await self.connection.execute(
            """
            UPDATE channel SET bot_name = ?, streamer_channel = ?, prefix = ?, coin_name = ?, income = ?, timeout = ? WHERE id = ?
        """,
            (
                self.bot_name,
                self.streamer_channel,
                self.prefix,
                self.coin_name,
                self.income,
                self.timeout,
                self.id,
            ),
        )

        await self.connection.commit()

    async def update_income(self, income: int):
        await self.connection.execute(
            """
            UPDATE channel SET income = ? WHERE streamer_channel = ?
        """,
            (income, self.streamer_channel),
        )

        await self.connection.commit()
        logger.debug(f"Income updated successfully with new value {income}.")

    async def get_channel(self, name: str) -> Channel:
        async with self.connection.execute(
            """
            SELECT * FROM channel WHERE streamer_channel = ?
        """,
            (name,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return Channel(*result)

    async def get_last_channel(self) -> Channel:
        async with self.connection.execute(
            """
            SELECT * FROM channel ORDER BY id DESC LIMIT 1
        """
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return Channel(*result)

    async def add_channel(self):
        await self.connection.execute(
            """
            INSERT INTO channel (bot_name, streamer_channel, prefix, coin_name, income, timeout) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                self.bot_name,
                self.streamer_channel,
                self.prefix,
                self.coin_name,
                self.income,
                self.timeout,
            ),
        )

        await self.connection.commit()
        logger.debug("Channel added successfully.")

    async def get_env(self):
        """
        Gets the environment variables.

        Parameters
        ----------
        None

        Returns
        -------
        cfg : dict
            The environment variables.
        """

        cfg = {}

        if os.getenv("TWITCH_SECRET_TOKEN"):
            cfg["TWITCH_SECRET_TOKEN"] = os.getenv("TWITCH_SECRET_TOKEN")
        else:
            cfg["TWITCH_SECRET_TOKEN"] = ""

        if os.getenv("TWITCH_CLIENT_TOKEN"):
            cfg["TWITCH_CLIENT_TOKEN"] = os.getenv("TWITCH_CLIENT_TOKEN")
        else:
            cfg["TWITCH_CLIENT_TOKEN"] = ""

        return cfg
