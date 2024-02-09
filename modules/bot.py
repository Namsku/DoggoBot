from modules.logger import Logger
from modules.user import UserCog
from modules.sfx import SFXCog
from modules.channel import ChannelCog
from modules.message import MessageCog
from modules.cmd import CmdCog, Cmd
from modules.games.common import GamesCog

import aiosqlite

from twitchio import ChannelFollowerEvent, Message
from twitchio.ext import commands
from twitchio.channel import Channel
from twitchio.user import User

# from twitchio.ext import eventsub

import os


class Bot(commands.Bot):
    def __init__(self, channel: ChannelCog) -> None:
        """
        Initializes a new bot object.

        Parameters
        ----------
        channel : ChannelCog
            The channel object.

        Returns
        -------
        None
        """

        self.token = self.get_twitch_secret_token()
        self.channel_id = channel.streamer_channel
        self.prefix = channel.prefix

        super().__init__(
            token=self.token,
            prefix=self.prefix,
            initial_channels=[self.channel_id],
        )

        self.active = False
        self.initialized = False

        self.bot_name = channel.bot_name
        self.user_bots = None
        self.client_id = self.get_twitch_client_token()

        self.channel_members = None
        self.coin_name = channel.coin_name
        self.logger = Logger(__name__)
        self.server = None

    async def __ainit__(self, channel: ChannelCog) -> None:
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
        await self._ainit_database_conn(channel)
        await self._ainit_database_classes(channel)
        await self._ainit_database_tables()
        await self._ainit_env()
        await self._ainit_user_commands()

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

    async def _ainit_database_conn(self, channel: ChannelCog) -> None:
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
        self.connection_channel = channel.connection
        self.connection_cmd = await aiosqlite.connect("data/database/cmd.sqlite")
        self.connection_message = await aiosqlite.connect("data/database/message.sqlite")
        self.connection_user = await aiosqlite.connect("data/database/user.sqlite")
        self.connection_sfx = await aiosqlite.connect("data/database/sfx.sqlite")
        self.connection_games = await aiosqlite.connect("data/database/games.sqlite")
        self.logger.debug("Database connection established.")

    async def _ainit_database_classes(self, channel: ChannelCog) -> None:
        """
        Initializes the database classes.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.channel = channel
        self.cmd = CmdCog(self.connection_cmd)
        self.msg = MessageCog(self.connection_message)
        self.usr = UserCog(channel, self.connection_user)
        self.sfx = SFXCog(self.connection_sfx)
        self.gms = GamesCog(self.connection_games)
        self.logger.debug("Database classes initialized.")

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
        await self.cmd.fill_default_table()
        await self.msg.create_table()
        await self.usr.create_table()
        await self.sfx.create_table()
        await self.gms.create_table()
        await self.gms.gambling.__ainit__()
        self.logger.debug("Tables created.")

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

    async def event_command_error(self, ctx: commands.Context, error: Exception) -> None:
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
        followers: [ChannelFollowerEvent] = await your_channel[0].fetch_channel_followers(self.token)

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

    @commands.command(name="slots")
    async def slots(self, ctx: commands.Context) -> None:
        """
        Slots game.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        user = ctx.author.name.lower()
        amount = ctx.content.split()[1]

        if await self.usr.get_balance(user) < amount:
            await ctx.send(f"{user} does not have enough coins.")
            return

        result = self.gms.get_slots_result()

        if result["status"]:
            await self.usr.update_user_balance(user, result["amount"])
            await ctx.send(f"{' '.join(result['spin'])} | {user} won {result['amount']} {self.coin_name}!")
        else:
            await self.usr.update_user_balance(user, -result["amount"])
            await ctx.send(f"{' '.join(result['spin'])} | {user} lost {result['amount']} {self.coin_name}!")

    @commands.command(name="gamble")
    async def gamble(self, ctx: commands.Context) -> None:
        """
        Gambles a certain amount of coins.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.content.split()) != 2:
            await ctx.send("Usage: !gamble <amount>")
            return

        user = ctx.author.name.lower()
        amount = ctx.content.split()[1]

        if not amount.isdigit():
            await ctx.send("Usage: !gamble <amount>")
            return

        amount = int(amount)

        if amount < 1:
            await ctx.send("Usage: !gamble <amount>")
            return

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        if await self.usr.get_balance(user) < amount:
            await ctx.send(f"{user} does not have enough coins.")
            return

        if self.gms.roll.maximum_bet < amount:
            await ctx.send(f"{user} cannot bet more than {self.gms.roll.maximum_bet} coins.")
            return

        if self.gms.roll.minimum_bet > amount:
            await ctx.send(f"{user} cannot bet less than {self.gms.roll.minimum_bet} coins.")
            return

        rng = self.gms.get_roll_number()

        # Critical Failure
        if rng == 0:
            # change amount has negative be sure it's integer without decimals
            amount = self.gms.roll.reward_critical_failure * amount
            amount = int(-amount)

            await self.usr.update_user_balance(user, amount)
            await ctx.send(f"{user} rolled an awful {rng} and lost {amount} {self.coin_name}!")
        elif rng == 100:
            amount = int(self.gms.roll.reward_critical_success * amount)
            await self.usr.update_user_balance(user, amount)
            await ctx.send(f"{user} rolled a perfect {rng} and won {amount} {self.coin_name}!")
        elif rng < 50:
            await self.usr.update_user_balance(user, -amount)
            await ctx.send(f"{user} rolled a {rng} and lost {amount} {self.coin_name}.")
        elif rng == 50:
            await ctx.send(f"{user} rolled a {rng} and nothing happened.")
        else:
            amount = int(2 * amount)
            await self.usr.update_user_balance(user, amount)
            await ctx.send(f"{user} rolled a {rng} and won {amount} {self.coin_name}!")

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
        -------
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
