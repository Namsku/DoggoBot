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

        self.router.add_api_route(
            "/api/chatters_stats", self.get_top_chatter, methods=["GET"]
        )
        self.router.add_api_route(
            "/api/users_stats", self.get_users_stats, methods=["GET"]
        )

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
                self.bot.super().__init__(
                    token=self.token,
                    prefix=self.prefix,
                    initial_channels=[self.channel_id],
                )

                await self.bot.__ainit__(self.bot.channel)
            except Exception as e:
                self.bot.logger.error(f"Error while initializing bot: {e}")
                message = {"error": str(e)}

        if self.bot.active:
            message.update(
                {
                    "bot_is_active": True,
                    "bot_is_configured": True,
                    "followers_count": len(await self.bot.user.get_followers()),
                    "subscriber_count": len(await self.bot.user.get_subscribers()),
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
        message = {}

        return self.templates.TemplateResponse(
            "chat.html", {"request": request, "message": message}
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
            self.bot.initial_channels = ([self.bot.channel.streamer_channel],)

            message = {
                "status": "success",
                "secret_token": bot_env["TWITCH_SECRET_TOKEN"],
                "client_token": bot_env["TWITCH_CLIENT_TOKEN"],
                "bot_name": self.bot.channel.bot_name,
                "streamer_channel": self.bot.channel.streamer_channel,
                "prefix": self.bot.channel.prefix,
                "coin_name": self.bot.channel.coin_name,
                "default_income": self.bot.channel.income,
                "default_timeout": self.bot.channel.timeout,
            }

            return self.templates.TemplateResponse(
                "settings.html", {"request": request, "message": message}
            )
        elif request.method == "GET":
            channel = await self.bot.channel.get_last_channel()
            bot_env = await self.bot.channel.get_env()

            message = {
                "status": "none",
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

    async def user(self, request: Request, name: str):
        message = {
            "user": await self.bot.user.get_user(name),
            "avatar": await self.bot.user.get_user_avatar(name),
        }
        return self.templates.TemplateResponse(
            "user.html", {"request": request, "message": message}
        )

    async def get_top_chatter(self):
        chatters = await self.bot.user.get_top5_chatters()
        return dumps(chatters, indent=None)

    def sort_dict_by_descending_values(self, dict1):
        temp = sorted(dict1.items(), key=lambda x: x[1], reverse=True)
        res = {k: v for k, v in temp}
        return res

    # Get the number of followers, subscribers, bots, and user without any of those roles
    async def get_users_stats(self):
        followers = await self.bot.user.get_followers()
        subscribers = await self.bot.user.get_subscribers()
        bots = await self.bot.user.get_user_bots()
        users = await self.bot.user.get_users_with_no_roles()

        results = {
            "followers": len(followers),
            "subscribers": len(subscribers),
            "bots": len(bots),
            "no roles": len(users),
        }

        return dumps(
            self.sort_dict_by_descending_values(results),
            indent=None,
        )
