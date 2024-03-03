from collections import OrderedDict
from dataclasses import asdict
import dataclasses

from modules.bot import Bot
from modules.cmd import Cmd
from modules.channel import Channel
from modules.logger import Logger


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
        self.logger = Logger(__name__)
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

        self.router.add_api_route(
            "/api/chatters_stats", self.get_top_chatter, methods=["GET"]
        )
        self.router.add_api_route(
            "/api/users_stats", self.get_users_stats, methods=["GET"]
        )
        self.router.add_api_route(
            "/api/rpg/events/{id}", self.get_all_rpg_events_by_id, methods=["GET"]
        )
        # self.router.add_api_route("/api/gatcha/events/{id}", self.get_all_gatch_events_by_id, methods=["GET"])
        self.router.add_api_route("/api/command", self.get_command, methods=["POST"])
        self.router.add_api_route("/api/rpg", self.get_rpg_event, methods=["POST"])
        self.router.add_api_route("/api/update", self.update_database, methods=["POST"])
        self.router.add_api_route(
            "/api/events/{type}/{id}", self.get_events, methods=["GET"]
        )

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

        self.router.add_api_route("/sounds", self.sounds, methods=["GET"])
        self.router.add_api_route("/sfx/{name}", self.sfx, methods=["GET"])

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

        # if get request has a query parameter, show it a a dictionary
        if request.query_params:
            message["oath"] = request.query_params

        # detect if the GET request has path started with #
        if request.url.path.startswith("/#"):
            # remove the # from the path
            # transform it to a oath dictionary
            message["oath"] = dict(
                [param.split("=") for param in request.url.path[2:].split("&")]
            )

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

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def get_events(self, request: Request, type: str, id: str):
        type_to_function = {
            "type": self.bot.gms.rpg.get_rpg_types_stats,
            "actions": self.bot.gms.rpg.get_rpg_actions_stats,
            "normal": self.bot.gms.rpg.get_rpg_normal_actions_stats,
            "treasure": self.bot.gms.rpg.get_rpg_treasure_actions_stats,
            "trap": self.bot.gms.rpg.get_rpg_trap_actions_stats,
            "monster": self.bot.gms.rpg.get_rpg_monster_actions_stats,
            "boss": self.bot.gms.rpg.get_rpg_boss_actions_stats,
        }

        func = type_to_function.get(type)
        if func:
            result = await func(id)
            return dumps(result)
        else:
            return dumps({})

    # parse content from the twitch oath redirect
    async def get_oath(self, request: Request):
        message = {}

        # if requests is a POST request, initialize the bot
        if request.method == "GET":
            try:
                message = request.query_params
            except Exception as e:
                self.bot.logger.error(f"Error while initializing bot: {e}")
                message = {"error": str(e)}

        # parse the query parameters in text format and indent the content
        # return is a very simplistic html page
        return dumps(message, indent=4)

    async def get_all_rpg_events_by_id(self, request: Request, id: int):
        message = {"events": await self.bot.gms.rpg.get_all_rpg_events_by_id(id)}

        self.bot.logger.debug(f"message: {message}")

        message = [asdict(event) for event in message["events"]]

        # remove the id from the list
        for event in message:
            event.pop("id")
            event.pop("rpg_id")

        # Return the content indent
        return dumps(message, indent=4)

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

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

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
            cmd_list.append(dataclasses.asdict(cmd))

        # Dynamic commands (The one created by users)
        cdyn: Cmd = await self.bot.cmd.get_all_dynamic_cmds()
        for cmd in cdyn:
            cdyn_list.append(dataclasses.asdict(cmd))

        message["prefix"] = self.bot.channel.channel.prefix
        message["based"] = cmd_list
        message["dynamic"] = cdyn_list

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def sounds(self, request: Request):
        """
        Returns the sfx page.

        Parameters
        ----------
        None

        Returns
        -------
        message : dict
            A dictionary containing the sfx's setting
        """

        message = {}
        message["sfx"] = await self.bot.sfx.get_all_sfx_groups()

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )
    
    async def sfx(self, request: Request, name: str):
        message = {}
        status = "none"

        if request.method == "POST":
            result = await self.save_rpg_settings(request)
            status = "error" if result.get("error") else "success"
            message[status] = result.get(status)

        message["status"] = status
        message["sfx"] = await self.bot.sfx.get_sfx_from_group_name(name)
        message["soundcards"] = self.bot.sfx.player.devices
        message["events"] = await self.bot.sfx.get_all_sfx_events_from_group_name(name)

        self.logger.debug(f"message: {message}")
        
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

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

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def overlay(self, request: Request):
        message = {}

        return self.templates.TemplateResponse(
            "overlay.html", {"request": request, "message": message}
        )

    async def games(self, request: Request):
        message = {}
        message["games"] = await self.bot.gms.get_all_games()
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def mods(self, request: Request):
        message = {}
        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

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

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

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

        self.bot.channel.update_environment_variables(
            {
                "secret_token": form.get("secret_token"),
                "client_token": form.get("client_token"),
                "decapi_secret_token": form.get("decapi_secret_token"),
            }
        )

        await self.bot.channel.update_channel(
            {
                "id": "1",
                "bot_name": form.get("bot_name"),
                "streamer_channel": form.get("streamer_channel"),
                "prefix": form.get("prefix"),
                "coin_name": form.get("coin_name"),
                "income": int(form.get("default_income")),
                "timeout": int(form.get("default_timeout")),
            }
        )

    async def get_bot_settings(self, channel: Channel) -> Optional[dict]:
        """Gets the bot's settings."""

        bot_env = await self.bot.channel.get_environment_variables()
        if bot_env is None:
            return None

        return {
            "secret_token": bot_env["TWITCH_SECRET_TOKEN"],
            "client_token": bot_env["TWITCH_CLIENT_TOKEN"],
            "decapi_secret_token": bot_env["DECAPI_SECRET_TOKEN"],
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

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def user(self, request: Request, name: str):
        message = {
            "user": await self.bot.usr.get_user(name),
            "avatar": await self.bot.usr.get_user_avatar(name),
        }

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

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
        self.bot.logger.debug(f"get_command -> json: {json}")

        for key, value in json.items():
            if key == "command":
                # convert cmd to json
                cmd = await self.bot.cmd.get_cmd(value)

                return dataclasses.asdict(cmd)

    async def get_rpg_event(self, request: Request) -> dict:
        """Gets a rpg event."""

        json = await request.json()
        self.bot.logger.debug(f"get_rpg_event -> json: {json}")

        for key, value in json.items():
            if key == "rpg":
                # convert cmd to json
                event = await self.bot.gms.rpg.get_rpg_event_by_id(value)

                return asdict(event)

    async def update_database(self, request: Request) -> dict:
        """Updates the database."""

        json = await request.json()
        self.logger.debug(f"json: {json}")

        # Define a dictionary to map keys to functions
        key_to_func = {
            "add_cmd": self.bot.cmd.add_cmd,
            "add_game": self.add_game,
            "add_event": self.bot.gms.rpg.add_rpg_event,
            "add_sfx": self.add_sfx,
            "cmd": self.update_cmd_status,
            "delete_game": self.delete_game,
            "delete_cmd": self.bot.cmd.delete_cmd,
            "delete_event": self.bot.gms.rpg.delete_rpg_event_by_id,
            "delete_sfx": self.bot.sfx.delete_sfx_group,
            "game": self.update_game_status,
            "import_event": self.import_events,
            "update_cmd": self.update_cmd,
            "update_event": self.update_event,
        }

        for key, value in json.items():
            self.logger.debug(f"key: {key}, value: {value}")
            func = key_to_func.get(key)
            self.logger.debug(f"func: {func}")
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

    async def update_event(self, value):
        self.logger.info(f"update_event -> value: {value}")
        return await self.bot.gms.rpg.update_rpg_event(value)

    async def add_sfx(self, value):
        # create the sfx profile
        sfx_result = await self.bot.sfx.add_sfx_group(value)

        return sfx_result

    async def add_game(self, value):

        # first we need to create the game in the database
        result = await self.bot.gms.add_game(value)

        # if the game was created successfully, we can add the game's profile
        if result.get("success"):

            # we need to check the category of the game
            category = value["category"].lower()

            # if the category is rpg, we need to create the rpg profile
            if category == "rpg":

                # create the rpg profile
                rpg_result = await self.bot.gms.rpg.add_rpg_profile(value["name"])

                # if the rpg profile wasn't created successfully, we need to delete the whole game
                if not rpg_result.get("success"):
                    await self.bot.gms.delete_game_by_name(value["name"])
                    return rpg_result  # Return the RPG failure result

                # if the rpg profile was created successfully, we need to fill the default events
                rpg_events_result = await self.bot.gms.rpg.fill_default_rpg_events(
                    await self.bot.gms.rpg.get_last_id()
                )

                # if the default events weren't created successfully, we need to delete the whole game
                if not rpg_events_result.get("success"):
                    await self.bot.gms.delete_game_by_name(value["name"])
                    return rpg_events_result

                return rpg_result
            elif category == "gatcha":
                return await self.bot.gms.add_gatcha(value)
        else:
            return result

    async def delete_game(self, value):
        # Delete the rpg events first
        rpg_id = await self.bot.gms.rpg.get_rpg_profile_id(value)

        rpg_events_result = await self.bot.gms.rpg.delete_all_rpg_events_by_id(rpg_id)

        # If the rpg events weren't deleted successfully, return the result
        if not rpg_events_result.get("success"):
            return rpg_events_result

        # Delete the rpg profile
        rpg_result = await self.bot.gms.rpg.delete_rpg_profile(value)

        # If the rpg profile wasn't deleted successfully, return the result
        if not rpg_result.get("success"):
            return rpg_result

        return await self.bot.gms.delete_game_by_name(value)

    async def rpg(self, request: Request, name: str):
        message = {}
        status = "none"

        if request.method == "POST":
            result = await self.save_rpg_settings(request)
            status = "error" if result.get("error") else "success"
            message[status] = result.get(status)

        message["status"] = status
        message["rpg"] = await self.bot.gms.rpg.get_rpg_profile_by_name(name)
        message["events"] = await self.bot.gms.rpg.get_all_rpg_events_by_id(
            message["rpg"].id
        )

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def gatcha(self, request: Request, name: str):
        message = {
            "gatcha": await self.bot.gms.get_gatcha(name),
        }

        return self.templates.TemplateResponse(
            "index.html", {"request": request, "message": message}
        )

    async def import_events(self, value):
        self.logger.debug(value)
        result = await self.bot.gms.rpg.delete_all_rpg_events_by_id(value["rpg_id"])

        self.logger.debug("Result -> {}".format(result))
        if result.get("error"):
            return result

        for event in value["import-file"]:
            ordered_dict = OrderedDict()
            ordered_dict["rpg_id"] = value["rpg_id"]
            ordered_dict["message"] = event["message"]
            ordered_dict["type"] = event["type"]
            ordered_dict["event"] = event["event"]

            # convert the ordered_dict to a regular dict
            event = dict(ordered_dict)

            self.logger.debug(f"Event -> {event}")
            result = await self.bot.gms.rpg.add_rpg_event(event)

            self.logger.debug("Result -> {}".format(result))
            if result.get("error"):
                return result

        return {"success": "Events imported successfully."}
