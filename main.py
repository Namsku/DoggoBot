from app.server import Server

from modules.bot import Bot
from modules.logger import Logger
from modules.channel import ChannelCog

from dotenv import load_dotenv
from fastapi import FastAPI

import asyncio
import aiosqlite
import os

logger = Logger(__name__)

from hypercorn.config import Config as HyperConfig
from hypercorn.asyncio import serve


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
        logger.error(f"Error while initializing bot: {e}")

    return bot


def security_check():
    """
    Checks if the script is running with admin privileges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    # if script is running as admin quit with error (all operating systems)
    if os.getuid() == 0:
        logger.error("Do not run this script as root!")
        exit(1)

    # if script is running with admin privileges quit with error (Windows)
    if os.name == "nt" and os.getenv("USERNAME") == "Administrator":
        logger.error("Do not run this script as Administrator!")
        exit(1)

    # if script is running with admin privileges quit with error (macOS)
    if os.name == "posix" and os.getuid() == 0:
        logger.error("Do not run this script as root!")
        exit(1)

    # if script is running with admin privileges quit with error (Linux)
    if os.name == "posix" and os.getenv("SUDO_USER") == "root":
        logger.error("Do not run this script as root!")
        exit(1)


async def main() -> None:
    load_dotenv()

    channel = await create_channel()
    bot = await create_bot(channel)

    app = FastAPI()
    server: Server = Server(bot, app)
    bot.server = server

    if not (os.getenv("TWITCH_SECRET_TOKEN") and os.getenv("TWITCH_CLIENT_TOKEN")):
        logger.warning(
            "Twitch tokens not found. Bot is not executed. Please add them on .env file or directly on the webapp."
        )
    elif bot.initialized == False:
        logger.warning(
            "Bot is not initialized. Please add the correct values on the webapp."
        )
    else:
        asyncio.create_task(bot.start())

    hyperconfig = HyperConfig()
    hyperconfig.bind = ["0.0.0.0:8000"]
    hyperconfig.worker_class = "asyncio"

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

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("CTRL+C pressed. Exiting...")
