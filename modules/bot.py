from modules.logger import Logger
from modules.user import UserCog
from modules.sfx import SFXCog
from modules.channel import ChannelCog
from modules.message import MessageCog

import aiosqlite

from twitchio import ChannelFollowerEvent, Message, Client
from twitchio.ext import commands
from twitchio.channel import Channel
from twitchio.user import User

from twitchio.ext import eventsub

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

        self.token = (
            os.getenv("TWITCH_SECRET_TOKEN")
            if os.getenv("TWITCH_SECRET_TOKEN")
            else "your-secret-token"
        )

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

        self.client_id = (
            os.getenv("TWITCH_CLIENT_TOKEN")
            if os.getenv("TWITCH_CLIENT_TOKEN")
            else "your-client-id"
        )

        self.channel_members = None
        self.coin_name = channel.coin_name
        self.logger = Logger(__name__)
        self.server = None

    async def __ainit__(self, channel: ChannelCog) -> None:
        self.connection_channel = channel.connection
        self.connection_message = await aiosqlite.connect(
            "data/database/message.sqlite"
        )
        self.connection_user = await aiosqlite.connect("data/database/user.sqlite")
        self.connection_sfx = await aiosqlite.connect("data/database/sfx.sqlite")
        self.logger.debug("Database connection established.")

        self.channel = channel
        self.sfx = SFXCog(self.connection_sfx)
        self.user = UserCog(self.channel, self.connection_user)
        self.message = MessageCog(self.connection_message)
        self.logger.debug("Cogs initialized.")

        await self.channel.create_table()
        await self.user.create_table()
        await self.sfx.create_table()
        self.logger.debug("Tables created.")

        if os.getenv("TWITCH_SECRET_TOKEN") and os.getenv("TWITCH_CLIENT_TOKEN"):
            await self.get_channel_members()
            self.logger.debug("Channel members fetched.")

            await self.user.get_bots()
            self.logger.debug("Bots fetched.")

            # await self.get_channel_mods()
            # self.logger.debug("Mods fetched.")

            await self.user.update_user_database(self.channel_members)
            self.logger.debug("Users updated.")

            self.initialized = True

    async def __aclose__(self) -> None:
        await self.connection_channel.close()
        await self.connection_user.close()
        await self.connection_sfx.close()

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
        await self.message.add_message(message)

        name = message.author.name.lower() if message.author else self.bot_name.lower()
        if not await self.user.get_user(name):
            await self.user.add_user(name)
            await self.user.increment_user_message_count(name)

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
        if not await self.user.get_user(user.name):
            await self.user.add_user(user.name)

        if await self.user.is_bot(user.name):
            await self.user.update_user_bot(user.name, True)

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

        self.user.mods = [
            mod.name.lower() for mod in await client.fetch_moderators(self.bot.token)
        ]

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
        user = await self.user.get_top_chatter()
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

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """
        Pings the bot.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """
        await ctx.send(f"Pong! {round(self.latency*1000)}ms")

    @commands.command(name="shoutout", aliases=["so"])
    async def shoutout(self, ctx: commands.Context) -> None:
        """
        Shoutouts a user.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 2:
            await ctx.send(f"Usage: !so <user>")
            return

        user = ctx.content.split()[1].lower().replace("@", "")

        await ctx.send(
            f" 📢 Please give a look to our Doggo >>> {user} <<<, "
            f"Take a look at his twitch channel (twitch.tv/{str.lower(user)})"
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
            await ctx.send(f"Usage: !topchatter")
            return

        user = await self.user.get_top_chatter()

        if user:
            await ctx.send(f"The top chatter is {user}")
        else:
            await ctx.send(f"No top chatter found.")

    @commands.command(name="mods")
    async def info_mods(self, ctx: commands.Context):
        '''
        Mods of the channel
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.
        
        Returns
        -------
        None
        '''
        await ctx.send("📢 If you search a list of good mods/tools for RE, everything is on my discord (!socials for more info)")

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
            await ctx.send(f"Usage: !balance")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has {await self.user.get_balance(user)} {self.coin_name}"
        )

    @commands.command(name="schedule")
    async def schedule(self, ctx: commands.Context):
        '''
        Schedule of the streamer
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.
            
        Returns
        -------
        None
        '''
        
        await ctx.send("📆 I am currently an irregular streamer due to some errands 🤗")

    @commands.command(name="help")
    async def help(self, ctx: commands.Context):
        '''
        Help command
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.
        
        Returns
        -------
        None
        '''
        
        await ctx.send("📢 available commands: !about !followage !followdate !gamble !help !income !mods !rpg !schedule !sfx !slots !so !socials !roll")

    @commands.command(name="sfx")
    async def sound_effects(self, ctx: commands.Context):
        '''
        Sound effects command
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.
        
        Returns
        -------
        None
        '''

        await ctx.send("📢 The full list is on my discord (!socials for more info)")

    @commands.command(name="clip")
    async def clip(self, ctx: commands.Context) -> None:
        """
        Creates a clip.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 1:
            await ctx.send(f"Usage: !clip")
            return

        await ctx.send(f"Creating clip...")
        await ctx.channel.create_clip()

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
            await ctx.send(f"Usage: !followdate")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has been following the channel since {await self.user.get_followdate(user)}"
        )
    
    @commands.command(name="about")
    async def about_bot(self, ctx: commands.Context):
        """
        About the bot.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object. 
        
        Returns
        -------
        None
        """

        link = "discord.gg/SjGyhS9T"
        await ctx.send(f"DoggoBot has been created by Namsku - If you want more info ping him on his Discord ({link})")


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
            await ctx.send(f"Usage: !followage")
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        await ctx.send(
            f"{user} has been following the channel for {await self.user.get_followage(user)}"
        )
    
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
            await ctx.send(f"Usage: !watchtime")
            return
        
        user = ctx.author.name.lower()
        
        if user not in self.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return
        
        await ctx.send(
            f"{user} has been watching the channel for {await self.user.get_watchtime(user)}"
        )

    # get all commands names
    async def get_commands(self) -> [str]:
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
        ccc = []

        for command in self.commands:
            ccc.append({
                "name": command.name,
                "description": "",
                "cost": 0,
                "used": 0,
                "status": "active"
            })
        
        return self.commands


        