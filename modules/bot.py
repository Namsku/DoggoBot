
from modules.logger import Logger
from modules.user import UserCog
from modules.sfx import SFXCog
from modules.channel import ChannelCog

import aiosqlite

from twitchio import ChannelFollowerEvent, Message, Client
from twitchio.ext import commands
from twitchio.channel import Channel
from twitchio.user import User

from twitchio.ext import eventsub

import os

class Bot(commands.Bot):
    def __init__(self, config: dict | None = None) -> None:
        '''
        Initializes a new bot object.
        
        Parameters
        ----------
        config : dict
            The configuration dictionary.
            
        Returns
        -------
        None
        '''

        self.token = os.getenv('SECRET_TOKEN')
        self.channel_id = config['streamer_channel']
        self.prefix = config['prefix']
        
        super().__init__(
            token=self.token,
            prefix=self.prefix,
            initial_channels=[self.channel_id],
        )

        self.bot_name = config['bot_name']
        self.client_id = os.getenv('CLIENT_TOKEN')
        self.coin_name = config['coin_name']
        self.logger = Logger(__name__)
        self.server = None

    async def __ainit__(self, config: dict) -> None:
        self.connection_channel = await aiosqlite.connect('data/database/channel.db')
        self.connection_user = await aiosqlite.connect('data/database/user.db')
        self.connection_sfx = await aiosqlite.connect('data/database/sfx.db')
        self.logger.debug('Database connection established.')

        self.channel = ChannelCog(config, self.connection_channel)
        self.sfx = SFXCog(self.connection_sfx)
        self.user = UserCog(self.channel, self.connection_user)
        self.logger.debug('Cogs initialized.')

        await self.get_channel_members()
        self.logger.debug('Channel members fetched.')

        await self.channel.create_table()
        await self.user.create_table()
        await self.sfx.create_table()
        self.logger.debug('Tables created.')

        if not await self.channel.get_channel(self.channel_id):
            await self.channel.add_channel()
            self.logger.debug('Channel added to database.')

        await self.user.get_bots()
        self.logger.debug('Bots fetched.')
        await self.user.update_user_database(self.channel_members)
        self.logger.debug('Users updated.')
        
    async def __aclose__(self) -> None:
        await self.connection_channel.close()
        await self.connection_user.close()
        await self.connection_sfx.close()

    async def update_config_values(self, config: dict) -> None:
        '''
        Updates the config values.
        
        Parameters
        ----------
        config : dict
            The configuration dictionary.
            
        Returns
        -------
        None
        '''
        self.prefix = config['prefix']
        self.channel_id = config['streamer_channel']
        self.prefix = config['prefix']
        self.bot_name = config['bot_name']
        self.coin_name = config['coin_name']

        self.logger.debug('Config values updated.')

    async def event_ready(self) -> None:
        '''
        Event called when the bot is ready.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        self.logger.info(f'Ready | {self.nick}')

    async def event_message(self, message: Message) -> None:
        '''
        Event called when a message is sent in the chat.
        
        Parameters
        ----------
        message : twitchio.Message
            The message object.
            
        Returns
        -------
        None
        '''
        name = message.author.name.lower() if message.author else self.bot_name.lower()
        if not await self.user.get_user(name):
            await self.user.add_user(name)
            await self.user.increment_user_message_count(name)

        self.logger.info(f'{name} -> {message.content}')
        return await super().event_message(message)
        
    async def event_command_error(self, ctx: commands.Context, error: Exception) -> None:
        '''
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
        '''
        self.logger.error(f'{ctx} -> {error}')

    async def event_command_error(self, ctx: commands.Context, error: Exception) -> None:
        '''
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
        '''
        self.logger.error(f'{ctx} -> {error}')

    async def event_join(self, channel: Channel, user: User):
        '''
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
        '''
        if not await self.user.get_user(user.name):
            await self.user.add_user(user.name)

        if await self.user.is_bot(user.name):
            await self.user.update_user_bot(user.name, True)
        
        self.logger.info(f'{user.name} joined {channel}')

    async def event_part(self, user: User):
        '''
        Event called when a user leaves the chat.
        
        Parameters
        ----------
        user : twitchio.User
            The user object.
            
        Returns4
        -------
        None
        '''
        self.logger.info(f'{user.name} left')
    
    async def get_channel_members(self) -> None:
        '''
        Gets the channel members.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        your_channel : [User] = await self.fetch_users([self.channel_id])
        followers : [ChannelFollowerEvent] = await your_channel[0].fetch_channel_followers(self.token)
        self.channel_members = [follower.user.name.lower() for follower in followers]

    async def get_top_chatter(self) -> str:
        '''
        Gets the top chatter.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        str
            The top chatter.
        '''
        user = await self.user.get_top_chatter()
        return user if user else None

    async def get_user_info(self, user: str) -> User:
        '''
        Gets the user info.
        
        Parameters
        ----------
        user : str
            The user name.
            
        Returns
        -------
        User
            The user object.
        '''
        

    @commands.command(name='ping')
    async def ping(self, ctx: commands.Context) -> None:
        '''
        Pings the bot.
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.
            
        Returns
        -------
        None
        '''
        await ctx.send(f'Pong! {round(self.latency*1000)}ms')   
    
    @commands.command(name='shoutout', aliases=['so'])
    async def shoutout(self, ctx: commands.Context) -> None:
        '''
        Shoutouts a user.
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        '''

        if len(ctx.message.content.split()) != 2:
            await ctx.send(f'Usage: !so <user>')
            return
    
        user = ctx.content.split()[1].lower().replace('@', '')

        await ctx.send(
            f" 📢 Please give a look to our Doggo >>> {user} <<<, " \
            f"Take a look at his twitch channel (twitch.tv/{str.lower(user)})"
        )  

    @commands.command(name='followage')
    async def followage(self, ctx: commands.Context) -> None:
        '''
        Gets the followage of a user.
        
        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        '''

        if len(ctx.message.content.split()) != 1:
            await ctx.send(f'Usage: !followage')
            return

        user = ctx.author.name.lower()

        if user not in self.channel_members:
            await ctx.send(f'{user} is not following the channel.')
            return

        await ctx.send(f'{user} has been following the channel for {await self.user.get_followage(user)}')