from typing import Union
from modules.logger import Logger

import aiosqlite
import dataclasses
import os


@dataclasses.dataclass
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
        """
        Initializes a new channel cog object.

        Parameters
        ----------
        connection : aiosqlite.Connection
            The connection to the database.

        Returns
        -------
        None
        """

        self.channel = None
        self.connection = connection
        self.logger = Logger(__name__)

    async def __ainit__(self) -> None:
        """
        Initializes the channel cog object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        if not await self.is_single_row_table():
            self.channel = self.get_default_config()
            await self.add_channel(self.channel)
        else:
            self.channel = await self.get_last_channel()

    def __str__(self) -> str:
        """
        Returns the string representation of the channel object.

        Parameters
        ----------
        None

        Returns
        -------
        str
            The string representation of the channel object.
        """

        return f"Channel(bot_name={self.bot_name}, streamer_channel={self.streamer_channel}, prefix={self.prefix}, coin_name={self.coin_name}, income={self.income}, timeout={self.timeout})"

    def update_environment_variables(self, config: dict) -> None:
        """
        Update the environment variables.

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
                file.write(f"TWITCH_SECRET_TOKEN={config.get('secret_token')}\n")
                file.write(f"TWITCH_CLIENT_TOKEN={config.get('client_token')}\n")
            # update the environment variables
            os.environ["TWITCH_SECRET_TOKEN"] = config.get("secret_token")
            os.environ["TWITCH_CLIENT_TOKEN"] = config.get("client_token")
        except Exception as e:
            self.logger.error(f"Error while writing the .env file: {e}")
            exit(1)

        self.logger.info("Environment variables updated successfully.")

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
        """
        Creates the table if it does not exist.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

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

    async def is_single_row_table(self) -> bool:
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

        return result[0] == 1

    async def update_channel(self, channel: Union[Channel, dict]) -> None:
        """
        Updates the channel with the given values.

        Parameters
        ----------
        channel : Union[Channel, dict]
            The channel to be updated.

        Returns
        -------
        None
        """

        if isinstance(channel, Channel):
            channel = dataclasses.asdict(channel)

        sql_query = f"UPDATE channel SET {', '.join(f'{key} = :{key}' for key in channel.keys())} WHERE id = :id"
        await self.connection.execute(sql_query, channel)
        await self.connection.commit()

    async def get_last_channel(self) -> Channel:
        """
        Gets the last channel from the database.

        Parameters
        ----------
        None

        Returns
        -------
        Channel
            The last channel from the database.
        """

        async with self.connection.execute(
            """
            SELECT * FROM channel ORDER BY id DESC LIMIT 1
        """
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return Channel(*result)

    async def add_channel(self, channel: Channel) -> None:
        """
        Adds a new channel to the database.

        Parameters
        ----------
        channel : Union[Channel, dict]
            The channel to be added.

        Returns
        -------
        None
        """

        try:
            await self.connection.execute(
                """
                INSERT INTO channel (id, bot_name, streamer_channel, prefix, coin_name, income, timeout) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    channel.id,
                    channel.bot_name,
                    channel.streamer_channel,
                    channel.prefix,
                    channel.coin_name,
                    channel.income,
                    channel.timeout,
                ),
            )

            await self.connection.commit()
            self.logger.info("Channel added successfully.")
        except Exception as e:
            self.logger.error(f"Error while adding the channel: {e}")
            raise

    async def get_environment_variables(self) -> dict:
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
        keys = ["TWITCH_SECRET_TOKEN", "TWITCH_CLIENT_TOKEN"]

        for key in keys:
            cfg[key] = os.getenv(key, "")

        return cfg
