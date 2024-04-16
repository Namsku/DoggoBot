from app.server import Server
from modules.bot import Bot
from modules.logger import Logger
from modules.channel import ChannelCog

from hypercorn.config import Config as HyperConfig
from hypercorn.asyncio import serve
from dotenv import load_dotenv
from fastapi import FastAPI

import asyncio
import aiosqlite
import os
import traceback

logger = Logger(__name__)


async def create_channel() -> ChannelCog:
    """
    Creates a channel object.

    Parameters
    ----------
    None

    Returns
    -------
    channel : ChannelCog
        The channel object.
    """

    connection_channel = await aiosqlite.connect("data/database/channel.sqlite")
    channel = ChannelCog(connection_channel)
    await channel.create_table()

    try:
        await channel.__ainit__()
    except Exception as e:
        logger.error(f"Error while initializing channel: {e}")

    return channel


async def create_bot(channel: ChannelCog) -> Bot:
    """
    Creates a bot object.

    Parameters
    ----------
    channel : ChannelCog
        The channel object.

    Returns
    -------
    bot : Bot
        The bot object.
    """

    bot = Bot(channel)

    try:
        await bot.__ainit__(channel)
        logger.debug("Bot initialized successfully.")
    except Exception as e:
        logger.error(f"Error while initializing bot: {e} - {traceback.format_exc()}")
        # logger.error(f"Error while initializing bot: {e}")

    return bot


def check_admin() -> bool:
    """Check if the script is running as root or administrator on any operating system.

    Returns:
        True if the script is running as root or administrator, False otherwise.
    """
    if os.name == "nt":
        # On Windows, the "SYSTEM" user is also an administrator.
        return os.getenv("USERNAME") in ["Administrator", "SYSTEM"]
    elif os.name == "posix":
        return os.getuid() == 0 or os.getenv("SUDO_USER") == "root"

    return False


def check_database() -> bool:
    """
    Checks if the database is initialized.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        True if the database is initialized, False otherwise.
    """

    if not os.path.exists("data/database"):
        return False

    if not os.path.exists("data/database/channel.sqlite"):
        return False

    if not os.path.exists("data/database/cmd.sqlite"):
        return False

    return True


def create_hyperconfig() -> HyperConfig:
    """
    Creates a Hypercorn configuration object.

    Parameters
    ----------
    None

    Returns
    -------
    hyperconfig : HyperConfig
        The Hypercorn configuration object.
    """

    hyperconfig = HyperConfig()
    hyperconfig.bind = ["0.0.0.0:80"]
    hyperconfig.worker_class = "asyncio"
    return hyperconfig


async def main() -> None:
    """
    The main entry point for the bot.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    load_dotenv()

    os.makedirs("data/database")


    channel = await create_channel()
    bot = await create_bot(channel)

    app = FastAPI()
    server: Server = Server(bot, app)
    bot.server = server

    if os.getenv("DOGGOBOT_SERVER_DBG") == "1":
        logger.debug("Debug mode enabled.")

    if not (os.getenv("TWITCH_SECRET_TOKEN") and os.getenv("TWITCH_CLIENT_TOKEN")):
        logger.warning(
            "Twitch tokens not found. Bot is not executed. Please add them on .env file or directly on the webapp."
        )
    elif not (os.getenv("DECAPI_SECRET_TOKEN")):
        logger.warning(
            "DecAPI token not found. Please add it on .env file or directly on the webapp."
        )
    elif not check_database():
        logger.warning("Database is not initialized. Please run the bot on the webapp.")
    elif bot.initialized is False:
        logger.warning(
            "Bot is not initialized. Please add the correct values on the webapp."
        )
    else:
        asyncio.create_task(bot.start())

    hyperconfig = create_hyperconfig()

    await serve(app, hyperconfig)


if __name__ == "__main__":
    """
    The main entry point for the bot.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    if check_admin():
        logger.error("Please do not run the bot as root or administrator.")
        exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("CTRL+C pressed. Exiting...")
