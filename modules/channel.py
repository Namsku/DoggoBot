import aiosqlite
import asyncio
from dataclasses import dataclass

from modules.logger import Logger

logger = Logger(__name__)


@dataclass
class Channel:
    bot_name: str
    streamer_channel: str
    prefix: str
    coin_name: str
    income: int
    timeout: int


class ChannelCog:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        if asyncio.create_task(self.is_table_empty()):
            channel = self.get_default_config()
        else:
            channel = self.get_last_channel()

        self.bot_name = channel.bot_name
        self.streamer_channel = channel.streamer_channel
        self.prefix = channel.prefix
        self.coin_name = channel.coin_name
        self.income = channel.income
        self.timeout = channel.timeout

        if asyncio.create_task(self.is_table_empty()):
            asyncio.create_task(self.add_channel())

        self.connection = connection

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

        self.bot_name = channel.bot_name
        self.streamer_channel = channel.streamer_channel
        self.prefix = channel.prefix
        self.coin_name = channel.coin_name
        self.income = channel.income
        self.timeout = channel.timeout

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
            "doggobot",
            input("Enter the streamer channel: "),
            "!",
            "DoggoCoin(s)",
            10000,
            5,
        )

    async def create_table(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS channel (
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

    async def is_table_empty(self) -> bool:
        """
        Checks if the table is empty.

        Parameters
        ----------
        None

        Returns
        -------
        result : bool
            True if the table is empty, False otherwise.
        """

        async with self.connection.execute(
            """
            SELECT * FROM channel
        """
        ) as cursor:
            result = await cursor.fetchone()

        return result is None

    async def update_channel(self):
        await self.connection.execute(
            """
            UPDATE channel bot_name = ?, streamer_channel = ?, prefix = ?, coin_name = ?, income = ?, timeout = ? WHERE id = ?
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
            INSERT INTO channel (streamer_channel, prefix, coin_name, income, timeout) VALUES (?, ?, ?, ?, ?)
        """,
            (
                self.streamer_channel,
                self.prefix,
                self.coin_name,
                self.income,
                self.timeout,
            ),
        )

        await self.connection.commit()
        logger.debug("Channel added successfully.")
