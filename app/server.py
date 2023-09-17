from modules.bot import Bot

from fastapi import FastAPI, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from json import dumps


class Server(Bot):
    def __init__(self, bot: Bot, app: FastAPI):
        self.bot = bot
        self.app = app
        self.templates = Jinja2Templates(directory="app/templates")
        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")
        self.router = APIRouter()

        self.router.add_api_route("/", self.home, methods=["GET", "POST"])
        self.router.add_api_route("/chat", self.chat, methods=["GET"])

        self.router.add_api_route("/curse", self.curse, methods=["GET"])
        self.router.add_api_route("/games", self.games, methods=["GET"])

        self.router.add_api_route("/mods", self.mods, methods=["GET"])
        self.router.add_api_route("/overlay", self.overlay, methods=["GET"])
        self.router.add_api_route("/rpg", self.rpg, methods=["GET"])
        self.router.add_api_route("/settings", self.settings, methods=["GET", "POST"])
        self.router.add_api_route("/sfx", self.sfx, methods=["GET"])

        self.router.add_api_route("/user/{name}", self.user, methods=["GET"])

        self.app.include_router(self.router)

    async def home(self, request: Request):
        message = {}

        if request.method == "POST":
            try:
                await self.bot.__ainit__(self.bot.channel)
            except Exception as e:
                self.bot.logger.error(f"Error while initializing bot: {e}")
                message = {"error": str(e)}

        if self.bot.active:
            message.update(
                {
                    "bot_is_active": True,
                    "bot_is_configured": True,
                    "followers_count": len(self.bot.channel_members),
                    "top_chatter": await self.bot.get_top_chatter(),
                }
            )
        else:
            message.update(
                {
                    "bot_is_active": False,
                    "bot_is_configured": self.bot.initialized,
                }
            )

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def chat(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def sfx(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def curse(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def overlay(self, request: Request):
        return self.templates.TemplateResponse(
            "overlay.html", {"request": request, "message": self.bot}
        )

    async def rpg(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def mods(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def games(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def settings(self, request: Request):
        if request.method == "POST":
            form = await request.form()

            cfg = {
                "secret_token": form.get("secret_token"),
                "client_token": form.get("client_token"),
                "bot_name": form.get("bot_name"),
                "streamer_channel": form.get("streamer_channel"),
                "prefix": form.get("prefix"),
                "coin_name": form.get("coin_name"),
                "default_income": int(form.get("default_income")),
                "default_timeout": int(form.get("default_timeout")),
            }

            self.bot.channel.set_env(cfg)
            await self.bot.channel.set_channel(cfg)

            bot_env = await self.bot.channel.get_env()

            self.bot.token = (bot_env["TWITCH_CLIENT_TOKEN"],)
            self.bot.prefix = (self.bot.channel.prefix,)
            self.bot.initial_channels = ([self.channel.streamer_channel],)

            message = {
                "secret_token": bot_env["TWTICH_SECRET_TOKEN"],
                "client_token": bot_env["TWITCH_CLIENT_TOKEN"],
                "bot_name": channel.bot_name,
                "streamer_channel": channel.streamer_channel,
                "prefix": channel.prefix,
                "coin_name": channel.coin_name,
                "default_income": channel.income,
                "default_timeout": channel.timeout,
            }

            return self.templates.TemplateResponse(
                "settings.html", {"request": request, "message": message}
            )
        elif request.method == "GET":
            channel = await self.bot.channel.get_last_channel()
            bot_env = await self.bot.channel.get_env()

            message = {
                "secret_token": bot_env["TWITCH_SECRET_TOKEN"],
                "client_token": bot_env["TWITCH_CLIENT_TOKEN"],
                "bot_name": channel.bot_name,
                "streamer_channel": channel.streamer_channel,
                "prefix": channel.prefix,
                "coin_name": channel.coin_name,
                "default_income": channel.income,
                "default_timeout": channel.timeout,
            }

            return self.templates.TemplateResponse(
                "settings.html", {"request": request, "message": message}
            )

    async def overlay(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "bot": self.bot}
        )

    async def user(self, request: Request, name: str):
        message = {
            "user": await self.bot.user.get_user(name),
            "avatar": await self.bot.user.get_user_avatar(name),
        }
        return self.templates.TemplateResponse(
            "user.html", {"request": request, "message": message}
        )
