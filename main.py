


from app.server import Server

from modules.bot import Bot
from modules.logger import Logger
from modules.config import Config

from dotenv import load_dotenv
from fastapi import FastAPI

import asyncio

logger = Logger(__name__)

from hypercorn.config import Config as HyperConfig
from hypercorn.asyncio import serve

async def main() -> None:
    load_dotenv()
    config = Config()
    bot = Bot(config.content)
    await bot.__ainit__(config.content)
    logger.debug("Bot initialized successfully.")

    app = FastAPI()
    server: Server = Server(bot, app)

    bot.server = server
    asyncio.create_task(bot.start())

    hyperconfig = HyperConfig()
    hyperconfig.bind = ['0.0.0.0:8000']
    hyperconfig.worker_class = 'asyncio'

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