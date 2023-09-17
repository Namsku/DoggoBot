
from modules.logger import Logger
from modules.channel import ChannelCog

import aiohttp
import aiosqlite
from dataclasses import dataclass

@dataclass
class User:
    # User settings
    id: int
    username: str
    income: int

    message_count: int

    bot: bool
    follower: bool
    subscriber: bool

    # Game/SFX settings
    gamble_lock: str
    roll_lock: str
    rpg_lock: str
    sfx_lock: str
    slots_lock: str

    # Moderation settings
    ban_time: str
    warning: int


class UserCog():
    def __init__(self, channel: ChannelCog, connection: aiosqlite.Connection):
        self.bots = None
        self.connection = connection
        self.channel = channel
        self.logger = Logger(__name__)

    async def get_bots(self) -> None:
        '''
        Gets a list of all bots from TwitchInsights.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.twitchinsights.net/v1/bots/all"
            ) as response:
                json_file = await response.json()

        if json_file:
            self.bots = [x[0] for x in json_file["bots"]]
    
    async def is_bot(self, username: str) -> bool:
        '''
        Checks if a user is a bot.
        
        Parameters
        ----------
        
        username : str
            The username to check.
            
        Returns
        -------
            bool
                True if the user is a bot, False otherwise.
        '''
        if self.bots is None:
            await self.get_bots()

        if username in self.bots:
            return True
        else:
            return False
        
    async def create_table(self):
        '''
        Creates a table in the database.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                income INTEGER,
                message_count INTEGER,
                bot INTEGER,
                follower INTEGER,
                subscriber INTEGER,
                gamble_lock TEXT,
                roll_lock TEXT,
                rpg_lock TEXT,
                sfx_lock TEXT,
                slots_lock TEXT,
                ban_time TEXT,
                warning INTEGER
            )
        """
        )

        await self.connection.commit()

    async def get_user(self, username: str) -> User:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE username = ?
        """,
            (username,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return User(*result)

    async def get_user_by_id(self, id: int) -> User:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE id = ?
        """,
            (id,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return User(*result)

    async def get_all_users(self) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def get_all_usernames(self) -> list[str]:
        async with self.connection.execute(
            """
            SELECT username FROM users
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [user[0] for user in result]

    async def get_followers(self) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE follower = 1
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def get_subscribers(self) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE subscriber = 1
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def get_banned(self) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE ban_time IS NOT NULL
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def get_warned(self) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE warning > 0
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def get_banned_by_time(self, time: str) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE ban_time = ?
        """,
            (time,),
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def get_warned_by_amount(self, amount: int) -> list[User]:
        async with self.connection.execute(
            """
            SELECT * FROM users WHERE warning = ?
        """,
            (amount,),
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [User(*user) for user in result]

    async def add_user(self, username: str) -> None:
        await self.connection.execute(
            """
            INSERT INTO users (
                username, 
                income, 
                message_count,
                bot, 
                follower, 
                subscriber, 
                gamble_lock, 
                roll_lock, 
                rpg_lock, 
                sfx_lock, 
                slots_lock, 
                ban_time, 
                warning
                )
            VALUES (
                ?, 
                ?, 
                0,
                0, 
                0, 
                0, 
                'unlocked',
                'unlocked', 
                'unlocked', 
                'unlocked', 
                'unlocked', 
                NULL, 
                0
            )
        """,
            (
                username,
                self.channel.income,
            ),
        )
        await self.connection.commit()

    async def delete_user(self, username: str) -> None:
        await self.connection.execute(
            """
            DELETE FROM users WHERE username = ?
        """,
            (username,),
        )
        await self.connection.commit()
    
    async def update_user_income(self, username: str, income: int) -> None:
        await self.connection.execute(
            """
            UPDATE users SET income = ? WHERE username = ?
        """,
            (income, username),
        )
        await self.connection.commit()

    async def update_user_bot(self, username: str, bot: bool) -> None:
        await self.connection.execute(
            """
            UPDATE users SET bot = ? WHERE username = ?
        """,
            (bot, username),
        )
        await self.connection.commit()
    
    async def update_user_follower(self, username: str, follower: bool) -> None:
        await self.connection.execute(
            """
            UPDATE users SET follower = ? WHERE username = ?
        """,
            (follower, username),
        )
        await self.connection.commit()
    
    async def update_user_subscriber(self, username: str, subscriber: bool) -> None:
        await self.connection.execute(
            """
            UPDATE users SET subscriber = ? WHERE username = ?
        """,
            (subscriber, username),
        )
        await self.connection.commit()
    
    async def update_user_gamble_lock(self, username: str, gamble_lock: str) -> None:
        await self.connection.execute(
            """
            UPDATE users SET gamble_lock = ? WHERE username = ?
        """,
            (gamble_lock, username),
        )
        await self.connection.commit()
    
    async def update_user_roll_lock(self, username: str, roll_lock: str) -> None:
        await self.connection.execute(
            """
            UPDATE users SET roll_lock = ? WHERE username = ?
        """,
            (roll_lock, username),
        )
        await self.connection.commit()
    
    async def update_user_rpg_lock(self, username: str, rpg_lock: str) -> None:
        await self.connection.execute(
            """
            UPDATE users SET rpg_lock = ? WHERE username = ?
        """,
            (rpg_lock, username),
        )
        await self.connection.commit()
    
    async def update_user_sfx_lock(self, username: str, sfx_lock: str) -> None:
        await self.connection.execute(
            """
            UPDATE users SET sfx_lock = ? WHERE username = ?
        """,
            (sfx_lock, username),
        )
        await self.connection.commit()
    
    async def update_user_slots_lock(self, username: str, slots_lock: str) -> None:
        await self.connection.execute(
            """
            UPDATE users SET slots_lock = ? WHERE username = ?
        """,
            (slots_lock, username),
        )
        await self.connection.commit()
    
    async def update_user_ban_time(self, username: str, ban_time: str) -> None:
        await self.connection.execute(
            """
            UPDATE users SET ban_time = ? WHERE username = ?
        """,
            (ban_time, username),
        )
        await self.connection.commit()
    
    async def update_user_warning(self, username: str, warning: int) -> None:
        await self.connection.execute(
            """
            UPDATE users SET warning = ? WHERE username = ?
        """,
            (warning, username),
        )
        await self.connection.commit()

    async def update_user_database(self, channel_members: list[str]) -> None:
        '''
        Updates the user database.
        
        Parameters
        ----------
        channel_members : list[str]
            A list of all users in the channel.
            
        Returns
        -------
        None
        '''
        usernames = await self.get_all_usernames()

        for username in channel_members:
            if username not in usernames:
                await self.add_user(username)
                await self.update_user_follower(username, True)
                self.logger.info(f"Added {username} to the database.")

        for username in usernames:
            if username not in channel_members:
                await self.update_user_follower(username, False)
                
    async def get_followage(self, username: str) -> str:
        '''
        Gets the followage of a user.
        
        Parameters
        ----------
        username : str
            The username to check.
            
        Returns
        -------
        str
            The followage of the user.
        '''
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://beta.decapi.me/twitch/followage/{self.channel.streamer_channel}/{username}"
            ) as response:
                followage = await response.text()

        return followage
    
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
        async with self.connection.execute(
            """
            SELECT username FROM users ORDER BY message_count DESC LIMIT 1
            """
                ) as cursor:
            result = await cursor.fetchone()

            if result is None:
                return None
            
            return result[0]

    async def increment_user_message_count(self, username: str) -> None:  
        '''
        Increments the message count of a user.
        
        Parameters
        ----------
        username : str
            The username to increment.
            
        Returns
        -------
        None
        '''
        user = await self.get_user(username)
        await self.connection.execute(
            """
            UPDATE users SET message_count = ? WHERE username = ?
        """,
            (user.message_count + 1, username),
        )
        await self.connection.commit()

    async def get_user_avatar(self, username: str) -> str:
        '''
        Gets the avatar of a user.
        
        Parameters
        ----------
        username : str
            The username to check.
            
        Returns
        -------
        str
            The avatar of the user.
        '''
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://decapi.me/twitch/avatar/{username}"
            ) as response:
                avatar = await response.text()

        return avatar