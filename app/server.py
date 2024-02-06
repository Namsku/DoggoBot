from modules.bot import Bot
from modules.cmd import Cmd
from modules.channel import Channel

import os
import arel

from fastapi import FastAPI, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Optional
from json import dumps


class Server(Bot):
    def __init__(self, bot: Bot, app: FastAPI):
        self.bot = bot
        self.app = app
        self.templates = Jinja2Templates(directory="app/templates")

        if _debug := os.getenv("DOGGOBOT_SERVER_DBG"):
            hot_reload = arel.HotReload(paths=[arel.Path("app"), arel.Path("modules")])
            app.add_websocket_route("/hot-reload", route=hot_reload, name="hot-reload")
            app.add_event_handler("startup", hot_reload.startup)
            app.add_event_handler("shutdown", hot_reload.shutdown)
            self.templates.env.globals["DEBUG"] = _debug
            self.templates.env.globals["hot_reload"] = hot_reload

        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")
        self.router = APIRouter()

        self.router.add_api_route("/", self.home, methods=["GET", "POST"])

        self.router.add_api_route("/api/chatters_stats", self.get_top_chatter, methods=["GET"])
        self.router.add_api_route("/api/users_stats", self.get_users_stats, methods=["GET"])
        self.router.add_api_route("/api/command", self.get_command, methods=["POST"])
        self.router.add_api_route("/api/update", self.update_database, methods=["POST"])

        self.router.add_api_route("/chat", self.chat, methods=["GET"])
        self.router.add_api_route("/commands", self.commands, methods=["GET"])
        self.router.add_api_route("/curse", self.curse, methods=["GET"])
        self.router.add_api_route("/gambling", self.gambling, methods=["GET", "POST"])
        self.router.add_api_route("/games", self.games, methods=["GET"])
        self.router.add_api_route("/rpg/{name}", self.rpg, methods=["GET", "POST"])
        self.router.add_api_route("/gatcha/{name}", self.gatcha, methods=["GET"])
        
        self.router.add_api_route("/mods", self.mods, methods=["GET"])
        self.router.add_api_route("/overlay", self.overlay, methods=["GET"])
        self.router.add_api_route("/settings", self.settings, methods=["GET", "POST"])
        self.router.add_api_route("/sfx", self.sfx, methods=["GET"])
        self.router.add_api_route("/user/{name}", self.user, methods=["GET"])

        self.app.include_router(self.router)

    async def home(self, request: Request):
        """
        Returns the home page.

        Parameters
        ----------
        None

        Returns
        -------
        message : dict
            A dictionary containing the bot's status.
        """

        message = {}

        # if requests is a POST request, initialize the bot
        if request.method == "POST":
            try:
                await self.bot.__ainit__(self.bot.channel)
            except Exception as e:
                self.bot.logger.error(f"Error while initializing bot: {e}")
                message = {"error": str(e)}

        # if the bot is active, return the bot's status
        if self.bot.active:
            message.update(
                {
                    "bot_is_active": True,
                    "bot_is_configured": True,
                    "followers_count": len(await self.bot.usr.get_followers()),
                    "subscriber_count": len(await self.bot.usr.get_subscribers()),
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

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def chat(self, request: Request):
        """
        Returns the chat page.

        Parameters
        ----------
        None

        Returns
        -------
        message : dict
            A dictionary containing the chat's settings.
        """

        message = {}

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def commands(self, request: Request):
        """
        Returns a list of commands.

        Parameters
        ----------
        None

        Returns
        -------
        message : dict
            A dictionary containing the list of commands.
        """

        cmd_list, cdyn_list = [[], []]
        message = {}

        cmds: Cmd = await self.bot.cmd.get_all_non_dynamic_cmds()

        # Classic commands (The one created by defaults)
        for cmd in cmds:
            cmd_list.append(self.bot.cmd.to_dict(cmd))

        # Dynamic commands (The one created by users)
        cdyn: Cmd = await self.bot.cmd.get_all_dynamic_cmds()
        for cmd in cdyn:
            cdyn_list.append(self.bot.cmd.to_dict(cmd))

        message["prefix"] = self.bot.channel.prefix
        message["based"] = cmd_list
        message["dynamic"] = cdyn_list

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def sfx(self, request: Request):
        """
        Returns the sfx page.

        Parameters
        ----------
        None

        Returns
        -------
        message : dict
            A dictionary containing the sfx's settings.
        """

        message = {}

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def curse(self, request: Request):
        """
        Returns the curse page.

        Parameters
        ----------
        None

        Returns
        -------
        message : dict
            A dictionary containing the curse's settings.
        """

        message = {}

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def overlay(self, request: Request):
        message = {}

        return self.templates.TemplateResponse("overlay.html", {"request": request, "message": message})

    async def games(self, request: Request):
        message = {}
        message["games"] = await self.bot.gms.get_all_games()
        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def mods(self, request: Request):
        message = {}
        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def save_gambling_settings(self, request: Request):
        """
        Saves the bot's settings.

        Parameters
        ----------
        request : Request
            The request object.

        Returns
        -------
        None
        """

        form = await request.form()
        result = await self.bot.gms.gambling.set_game(form)

        return result
    
    async def save_rpg_settings(self, request: Request):
        """
        Saves the bot's settings.

        Parameters
        ----------
        request : Request
            The request object.

        Returns
        -------
        None
        """

        form = await request.form()
        result = await self.bot.gms.rpg.set_rpg(form)

        return result

    async def gambling(self, request: Request):
        message = {}
        status = "none"

        if request.method == "POST":
            result = await self.save_gambling_settings(request)
            status = "error" if result.get("error") else "success"
            message[status] = result.get(status)

        message["slots"] = await self.bot.gms.gambling.get_slots()
        message["roll"] = await self.bot.gms.gambling.get_roll()
        message["status"] = status

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def save_bot_settings(self, request: Request):
        """
        Saves the bot's settings.

        Parameters
        ----------
        request : Request
            The request object.

        Returns
        -------
        None
        """

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

    async def get_bot_settings(self, channel: Channel) -> Optional[dict]:
        """Gets the bot's settings."""

        bot_env = await self.bot.channel.get_env()
        if bot_env is None:
            return None

        return {
            "secret_token": bot_env["TWITCH_SECRET_TOKEN"],
            "client_token": bot_env["TWITCH_CLIENT_TOKEN"],
            "bot_name": channel.bot_name,
            "streamer_channel": channel.streamer_channel,
            "prefix": channel.prefix,
            "coin_name": channel.coin_name,
            "default_income": channel.income,
            "default_timeout": channel.timeout,
        }

    async def settings(self, request: Request):
        """Settings page."""

        channel = await self.bot.channel.get_last_channel()
        bot_settings = await self.get_bot_settings(channel)
        status = "none"

        if request.method == "POST":
            await self.save_bot_settings(request)
            bot_settings = await self.get_bot_settings(channel)
            status = "success"

        message = {
            "status": status,
            **bot_settings,
        }

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def user(self, request: Request, name: str):
        message = {
            "user": await self.bot.usr.get_user(name),
            "avatar": await self.bot.usr.get_user_avatar(name),
        }

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})

    async def get_top_chatter(self):
        chatters = await self.bot.usr.get_top5_chatters()
        return dumps(chatters, indent=None)

    def sort_dict_by_descending_values(self, dict1):
        temp = sorted(dict1.items(), key=lambda x: x[1], reverse=True)
        res = {k: v for k, v in temp}
        return res

    # Get the number of followers, subscribers, bots, and user without any of those roles
    async def get_users_stats(self):
        followers = await self.bot.usr.get_followers()
        subscribers = await self.bot.usr.get_subscribers()
        bots = await self.bot.usr.get_user_bots()
        users = await self.bot.usr.get_users_with_no_roles()

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

    async def get_command(self, request: Request) -> dict:
        """Gets a command."""

        json = await request.json()
        print(json)

        for key, value in json.items():
            if key == "command":
                # convert cmd to json
                cmd = await self.bot.cmd.get_cmd(value)

                return self.bot.cmd.to_dict(cmd)

    async def update_database(self, request: Request) -> dict:
        """Updates the database."""

        json = await request.json()
        self.bot.logger.debug(f"json: {json}")

        # Define a dictionary to map keys to functions
        key_to_func = {
            "add_cmd": self.bot.cmd.add_cmd,
            "add_game": self.add_game,
            "cmd": self.update_cmd_status,
            "delete_game": self.delete_game,
            "delete_cmd": self.bot.cmd.delete_cmd,
            "game": self.update_game_status,
            "update_cmd": self.update_cmd,
        }

        for key, value in json.items():
            func = key_to_func.get(key)
            if func:
                return await func(value)

        # If no matching key was found, return an error message
        return {"error": "Invalid key"}

    async def update_cmd_status(self, value):
        status = True if value["status"] == 1 else False
        return await self.bot.cmd.update_status(value["name"], status)

    async def update_cmd(self, value):
        return await self.bot.cmd.update_cmd(value["name"], value)

    async def update_game_status(self, value):
        status = True if value["status"] == 1 else False
        return await self.bot.gms.update_status(value["name"], status)

    async def add_game(self, value):
        result = await self.bot.gms.add_game(value)
        if result.get("success"):
            category = value["category"].lower()
            if category == "rpg":
                rpg_result = await self.bot.gms.rpg.add_rpg_profile(value['name'])
                if not rpg_result.get("success"):
                    await self.bot.gms.delete_game_by_name(value['name'])
                    return rpg_result  # Return the RPG failure result
                return rpg_result
            elif category == "gatcha":
                return await self.bot.gms.add_gatcha(value)
        else:
            return result
    
    async def delete_game(self, value):
        # Delete the rpg game first
        rpg_result = await self.bot.gms.rpg.delete_rpg_profile(value)
        if rpg_result.get("success"):
            return await self.bot.gms.delete_game_by_name(value)
        else:
            return rpg_result

    async def rpg(self, request: Request, name: str):
        message = {
            "status": "none"
        }

        if request.method == "POST":
            result = await self.save_rpg_settings(request)
            status = "error" if result.get("error") else "success"
            message["status"] = status

        message["rpg"] = await self.bot.gms.rpg.get_rpg_profile_by_name(name)
        

        self.bot.logger.debug(f"message: {message}")

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})
    
    async def gatcha(self, request: Request, name: str):
        message = {
            "gatcha": await self.bot.gms.get_gatcha(name),
        }

        return self.templates.TemplateResponse("index.html", {"request": request, "message": message})