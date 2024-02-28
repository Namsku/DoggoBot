from modules.channel import ChannelCog
from modules.cmd import CmdCog, Cmd
from modules.games.common import GamesCog
from modules.logger import Logger
from modules.message import MessageCog
from modules.sfx import SFXCog
from modules.user import UserCog

from twitchio import ChannelFollowerEvent, Message
from twitchio.channel import Channel
from twitchio.ext import commands
from twitchio.user import User

import os
import aiosqlite


class Bot(commands.Bot):
    def __init__(self, channel_cog: ChannelCog) -> None:
        """
        Initializes a new bot object.

        Parameters
        ----------
        channel_cog : ChannelCog
            The channel object.

        Returns
        -------
        None
        """

        self.token = self.get_twitch_secret_token()
        self.decapi_token = self.get_decapi_secret_token()
        self.channel_id = channel_cog.channel.streamer_channel
        self.prefix = channel_cog.channel.prefix

        super().__init__(
            token=self.token,
            prefix=self.prefix,
            initial_channels=[self.channel_id],
        )

        self.active = False
        self.initialized = False

        self.bot_name = channel_cog.channel.bot_name
        self.user = None
        self.user_bots = None
        self.client_id = self.get_twitch_client_token()

        self.channel_members = None
        self.coin_name = channel_cog.channel.coin_name
        self.logger = Logger(__name__)
        self.server = None

    async def __ainit__(self, channel_cog: ChannelCog) -> None:
        """
        Initializes the bot object.

        Parameters
        ----------
        channel : ChannelCog
            The channel object.

        Returns
        -------
        None
        """
        await self._ainit_database_conn(channel_cog)
        await self._ainit_database_classes(channel_cog)
        await self._ainit_cogs()
        await self._ainit_database_tables()
        await self._ainit_env()
        await self._ainit_user_commands()

    async def _ainit_database_conn(self, channel_cog: ChannelCog) -> None:
        """
        Initializes the database connection.

        Parameters
        ----------
        channel : ChannelCog
            The channel object.

        Returns
        -------
        None
        """
        self.connection_channel = channel_cog.connection
        self.connection_cmd = await aiosqlite.connect("data/database/cmd.sqlite")
        self.connection_message = await aiosqlite.connect(
            "data/database/message.sqlite"
        )
        self.connection_user = await aiosqlite.connect("data/database/user.sqlite")
        self.connection_sfx = await aiosqlite.connect("data/database/sfx.sqlite")
        self.connection_games = await aiosqlite.connect("data/database/games.sqlite")
        self.logger.debug("Database connection established.")

    async def _ainit_database_classes(self, channel_cog: ChannelCog) -> None:
        """
        Initializes the database classes.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.channel = channel_cog
        self.cmd = CmdCog(self.connection_cmd, self)
        self.msg = MessageCog(self.connection_message)
        self.usr = UserCog(channel_cog, self.connection_user)
        self.sfx = SFXCog(self.connection_sfx)
        self.gms = GamesCog(self.connection_games, self)
        self.logger.info("Database classes initialized.")

    async def _ainit_cogs(self) -> None:
        """
        Adds the Cog classes to the bot.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.add_cog(self.cmd)
        self.add_cog(self.msg)
        self.add_cog(self.usr)
        self.add_cog(self.sfx)
        self.add_cog(self.gms)
        self.add_cog(self.gms.gambling)
        self.logger.info("Cogs added to the bot.")

    async def _ainit_database_tables(self) -> None:
        """
        Initializes the database tables.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        await self.channel.create_table()
        await self.cmd.create_table()
        await self.msg.create_table()
        await self.usr.create_table()
        await self.sfx.create_table()
        await self.gms.create_table()

        await self.gms.gambling.__ainit__()
        self.logger.debug("Tables created.")

    async def __aclose__(self) -> None:
        """
        Closes the bot object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        await self.connection_channel.close()
        await self.connection_user.close()
        await self.connection_sfx.close()

    async def _ainit_user_commands(self) -> None:
        """
        Initializes the user commands.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        cmds = await self.cmd.get_user_cmds()
        for cmd in cmds:
            if cmd.status:
                self.add_command(commands.Command(cmd.name, self.template_command))

        self.logger.debug(f"User commands initialized. {len(cmds)}")

    async def _get_channel_members(self) -> None:
        """
        Fetches the channel members and stores them in the object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        await self.get_channel_members()
        self.logger.debug("Channel members fetched.")

    async def _get_user_bots(self) -> None:
        """
        Fetches the user's bots and stores them in the object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.user_bots = await self.usr.get_bots()
        self.logger.debug("Bots fetched.")

    async def _update_user_database(self) -> None:
        """
        Updates the user database with the channel members and bots.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        await self.usr.update_user_database(self.channel_members)
        self.logger.debug("Users updated.")

    async def _ainit_env(self) -> None:
        """
        Initializes the environment variables.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if os.getenv("TWITCH_SECRET_TOKEN") and os.getenv("TWITCH_CLIENT_TOKEN"):
            await self._get_channel_members()
            await self._get_user_bots()
            await self._update_user_database()

            self.initialized = True

    def get_decapi_secret_token(self) -> str:
        """
        Gets the DecAPI secret token from the environment variables.
        
        Returns
        -------
        str
            The DecAPI secret token.
        """
        token = os.getenv("DECAPI_SECRET_TOKEN")
        if token is None:
            raise RuntimeError("DECAPI_SECRET_TOKEN environment variable is not set.")
        return token

    def get_twitch_secret_token(self) -> str:
        """
        Gets the Twitch secret token from the environment variables.

        Returns
        -------
        str
            The Twitch secret token.
        """

        token = os.getenv("TWITCH_SECRET_TOKEN")
        if token is None:
            raise RuntimeError("TWITCH_SECRET_TOKEN environment variable is not set.")
        return token

    def get_twitch_client_token(self) -> str:
        """
        Gets the Twitch client token from the environment variables.

        Returns
        -------
        str
            The Twitch client token.
        """

        token = os.getenv("TWITCH_CLIENT_TOKEN")
        if token is None:
            raise RuntimeError("TWITCH_CLIENT_TOKEN environment variable is not set.")
        return token

    async def update_config_values(self, channel: Channel) -> None:
        """
        Updates the config values.

        Parameters
        ----------
        channel : Channel

        Returns
        -------
        None
        """
        self.prefix = channel.prefix
        self.channel_id = channel.streamer_channel
        self.coin_name = channel.coin_name
        self.income = channel.income
        self.timeout = channel.timeout

        self.logger.debug("Config values updated.")

    async def event_ready(self) -> None:
        """
        Event called when the bot is ready.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.active = True
        self.logger.info(f"Ready | {self.nick}")

    async def event_message(self, message: Message) -> None:
        """
        Event called when a message is sent in the chat.

        Parameters
        ----------
        message : twitchio.Message
            The message object.

        Returns
        -------
        None
        """
        name = message.author.name.lower() if message.author else self.bot_name.lower()

        if name != self.bot_name.lower():
            await self.msg.add_message(message, self)

        if not await self.usr.get_user(name):
            await self.usr.add_user(name)
            await self.usr.increment_user_message_count(name)

        self.logger.info(f"{name} -> {message.content}")
        return await super().event_message(message)

    async def event_command_error(
        self, ctx: commands.Context, error: Exception
    ) -> None:
        """
        Event called when a command error occurs.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.
        error : Exception
            The error object.

        Returns
        -------
        None
        """
        self.logger.error(f"{ctx} -> {error}")

    async def event_join(self, channel: Channel, user: User):
        """
        Event called when a user joins the chat.

        Parameters
        ----------
        channel : twitchio.Channel
            The channel object.
        user : twitchio.User
            The user object.

        Returns
        -------
        None
        """
        if not await self.usr.get_user(user.name):
            await self.usr.add_user(user.name)

        if await self.usr.is_bot(user.name):
            await self.usr.update_user_bot(user.name, True)

        self.logger.info(f"{user.name} joined {channel}")

    async def event_part(self, user: User):
        """
        Event called when a user leaves the chat.

        Parameters
        ----------
        user : twitchio.User
            The user object.

        Returns
        -------
        None
        """
        self.logger.info(f"{user.name} left")

    '''
    async def get_channel_mods(self) -> None:
        """
        Gets the channel mods.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.usr.mods = [mod.name.lower() for mod in await client.fetch_moderators(self.token)]
    '''

    async def get_channel_members(self) -> None:
        """
        Gets the channel members.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        your_channel: [User] = await self.fetch_users([self.channel_id])
        followers: [ChannelFollowerEvent] = await your_channel[
            0
        ].fetch_channel_followers(self.token)

        self.user = await self.fetch_users([self.channel_id])
        self.user = self.user[0]
        self.channel_members = [follower.user.name.lower() for follower in followers]

    async def get_top_chatter(self) -> str:
        """
        Gets the top chatter.

        Parameters
        ----------
        None

        Returns
        -------
        str
            The top chatter.
        """
        user = await self.usr.get_top_chatter()
        return user if user else None

    async def get_user_info(self, user: str) -> User:
        """
        Gets the user info.

        Parameters
        ----------
        user : str
            The user name.

        Returns
        -------
        User
            The user object.
        """

    # get all commands names
    async def get_all_commands(self) -> [Cmd]:
        """
        Gets all commands names.

        Parameters
        ----------
        None

        Returns
        -------
        [str]
            The commands names.
        """
        return await self.cmd.get_all_cmds()

    async def get_user_commands(self) -> [Cmd]:
        """
        Gets all commands names.

        Parameters
        ----------
        None

        Returns
        -------
        [str]
            The commands names.
        """
        return await self.cmd.get_user_cmds()

    async def add_cmd(self, cmd: Cmd) -> None:
        """
        Adds a command.

        Parameters
        ----------
        cmd : Cmd
            The command object.

        Returns
        -------±
        None
        """
        await self.cmd.add_cmd(cmd)
        await self.add_command(commands.Command(cmd.name, self.template_command))

    async def remove_cmd(self, cmd: Cmd) -> None:
        """
        Removes a command.

        Parameters
        ----------
        cmd : Cmd
            The command object.

        Returns
        -------
        None
        """
        await self.cmd.remove_cmd(cmd)
        await self.remove_command(cmd.name)

    async def disable_cmd(self, cmd: Cmd) -> None:
        """
        Disables a command.

        Parameters
        ----------
        cmd : Cmd
            The command object.

        Returns
        -------
        None
        """
        await self.cmd.disable_cmd(cmd)
        await self.remove_command(cmd.name)

    async def enable_cmd(self, cmd: Cmd) -> None:
        """
        Enables a command.

        Parameters
        ----------
        cmd : Cmd
            The command object.

        Returns
        -------
        None
        """
        await self.cmd.enable_cmd(cmd)
        self.add_command(commands.Command(cmd.name, self.template_command))

    # create a generic template for adding your own commands
    async def template_command(self, ctx: commands.Context) -> None:
        """
        Template command.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        self.logger.debug(f'User command named "{ctx.command.name}" called')
        cmd: Cmd = await self.cmd.get_cmd(ctx.command.name)

        if len(ctx.message.content.split()) != 1:
            await ctx.send(f"Usage: !{cmd.name}")
            return

        content = cmd.description
        await ctx.send(f"{content}")

    
    @commands.command(name="balance")
    async def balance(self, ctx: commands.Context) -> None:
        """
        Gets the balance of a user.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 1:
            await ctx.send("Usage: !balance")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has {await self.usr.get_balance(user)} {self.coin_name}"
        )

    @commands.command(name="followdate")
    async def followdate(self, ctx: commands.Context) -> None:
        """
        Gets the followdate of a user.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 1:
            await ctx.send("Usage: !followdate")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has been following the channel since {await self.usr.get_followdate(user)}"
        )

    @commands.command(name="followage")
    async def followage(self, ctx: commands.Context) -> None:
        """
        Gets the followage of a user.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 1:
            await ctx.send("Usage: !followage")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has been following the channel for {await self.usr.get_followage(user)}"
        )


    @commands.command(name="topchatter")
    async def topchatter(self, ctx: commands.Context) -> None:
        """
        Gets the top chatter.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 1:
            await ctx.send("Usage: !topchatter")
            return

        user = await self.get_top_chatter()

        if user:
            await ctx.send(f"The top chatter is {user}")
        else:
            await ctx.send("No top chatter found.")

    @commands.command(name="watchtime")
    async def watchtime(self, ctx: commands.Context) -> None:
        """
        Gets the watchtime of a user.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 1:
            await ctx.send("Usage: !watchtime")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has been watching the channel for {await self.usr.get_watchtime(user)}"
        )

    @commands.command(name="add")
    async def add(self, ctx: commands.Context) -> None:
        """
        Adds two numbers together.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """
        if ctx.author.name.lower() != self.channel.channel.streamer_channel:
            await ctx.send("You do not have permission to use this command.")
            return

        if len(ctx.message.content.split()) != 3:
            await ctx.send("Usage: !add <user> <number>")
            return

        try:
            user = ctx.message.content.split()[1].replace("@", "").lower()
            # check user exists
            if user not in self.channel_members:
                await ctx.send(f"{user} is not following the channel.")
                return

            num = int(ctx.message.content.split()[2])
            
            if num < 0:
                await ctx.send("Usage: !add <user> <number>")
                return

            await self.usr.update_user_income(user, num)
            await ctx.send(f"{user} has been awarded {num} {self.coin_name}")
        except ValueError:
            await ctx.send("Usage: !add <user> <number>")