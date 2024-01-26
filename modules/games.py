
from dataclasses import dataclass
from modules.logger import Logger

import aiosqlite
import random
import time

@dataclass
class Roll:
    status: int
    minimum_bet: int
    maximum_bet: int
    reward_critical_success: float
    reward_critical_failure: float

@dataclass
class Slots:
    cost: int
    status: int
    rng_manipulation: int
    success_rate: int
    reward_mushroom: float
    reward_coin: float
    reward_coin: float
    reward_leaf: float
    reward_diamond: float
    jackpot: int

class GamesCog:
    def __init__(self, connection: aiosqlite.Connection):
        '''
        Initialize the GamesCog class.
        
        Parameters
        ----------
        connection : aiosqlite.Connection
            Connection to the database.
        
        Returns
        -------
        None
        '''
        
        self.connection = connection
        self.logger = Logger(__name__)
        self.roll = None
        self.slots = None

    async def __ainit__(self) -> None:
        '''
        Initialize the GamesCog class.

        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''

        self.logger.info("Initializing GamesCog...")
        if await self.is_slots_table_empty():
            self.logger.info("Slots table not configured. Filling")
            await self.fill_default_slots_table()

        if await self.is_roll_table_empty():
            await self.fill_default_roll_table()

        self.slots = await self.get_slots()
        self.roll = await self.get_roll()

        self.logger.info("GamesCog initialized.")

    async def create_table(self):
        '''
        Create the games table for rolls and slots.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''

        ## create two table in one single execute
        await self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS slots (
                cost INTEGER NOT NULL,
                status INTEGER NOT NULL,
                rng_manipulation INTEGER NOT NULL,
                success_rate INTEGER NOT NULL,
                reward_mushroom REAL NOT NULL,
                reward_coin REAL NOT NULL,
                reward_leaf REAL NOT NULL,
                reward_diamond REAL NOT NULL,
                jackpot INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS roll (
                status INTEGER NOT NULL,
                minimum_bet INTEGER NOT NULL,
                maximum_bet INTEGER NOT NULL,
                reward_critical_success REAL NOT NULL,
                reward_critical_failure REAL NOT NULL
            );
        """
        )

    async def is_slots_table_empty(self) -> bool:
        """
        Checks if the table is empty.

        Returns
        -------
        bool
            True if the table is empty, False otherwise.
        """

        async with self.connection.execute("SELECT * FROM slots") as cursor:
            return not bool(await cursor.fetchone())

    async def is_roll_table_empty(self) -> bool:
        '''
        Check if the roll table is configured.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        bool
            True if the table is configured, False otherwise.
        '''
        
        async with self.connection.execute("SELECT * FROM roll") as cursor:
            return not bool(await cursor.fetchone())

    async def fill_default_slots_table(self):
        '''
        Fill the slots table with default values.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        
        await self.connection.execute(
            "INSERT INTO slots (cost, status, rng_manipulation, success_rate, reward_mushroom, reward_coin, reward_leaf, reward_diamond, jackpot) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                1,
                1,
                0,
                0,
                1.5,
                0.5,
                0.5,
                0.5,
                100,
            ),
        )
        await self.connection.commit()
        self.logger.info("Slots table filled.")

    async def fill_default_roll_table(self):
        '''
        Fill the roll table with default values.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''

        await self.connection.execute(
            "INSERT INTO roll (status, minimum_bet, maximum_bet, reward_critical_success, reward_critical_failure) VALUES (?, ?, ?, ?, ?)",
            (
                1,
                1,
                100,
                1.5,
                0.5,
            ),
        )
        await self.connection.commit()
        self.logger.info("Roll table filled.")

    async def get_roll(self) -> Roll:
        '''
        Get the roll object.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        Roll
            The roll object.
        '''

        return self.generate_random_number() 

    async def get_slot_spin(self) -> list:
        '''
        Get the result of a slot machine.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''

        symbols = ['🍄', '🪙', '🍀', '💎','💰']
        reels = [random.choice(symbols) for _ in range(3)]
        
        if self.slots.success_rate < 0:
            return reels

        if self.slots.success_rate >= self.generate_random_number():
            while not all(symbol == reels[0] for symbol in reels):
                reels = [random.choice(symbols) for _ in range(3)]

        return reels

    async def generate_random_number(self, min=0, max=100) -> int:
        '''
        Generate a random number between min and max.
        
        Parameters
        ----------
        min : int
            The minimum number to generate.
        max : int
            The maximum number to generate.
        
        Returns
        -------
        int
            The generated number.
        '''

        random.seed(time.time()**2 % 1000000)
        return random.randint(min, max)
    
    async def get_slots(self) -> Slots:
        '''
        Get the slots object.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        Slots
            The slots object.
        '''

        async with self.connection.execute(
            """
            SELECT * FROM slots
        """
        ) as cursor:
            slots = await cursor.fetchone()

            slots = Slots(
                cost=slots[0],
                status=slots[1],
                rng_manipulation=slots[2],
                success_rate=slots[3],
                reward_mushroom=slots[4],
                reward_coin=slots[5],
                reward_leaf=slots[6],
                reward_diamond=slots[7],
                jackpot=slots[8],
            )

        return slots
    
    async def get_roll(self) -> Roll:
        '''
        Get the roll object.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        Roll
            The roll object.
        '''

        async with self.connection.execute(
            """
            SELECT * FROM roll
        """
        ) as cursor:
            self.roll = await cursor.fetchone()

            roll = Roll(
                status=self.roll[0],
                minimum_bet=self.roll[1],
                maximum_bet=self.roll[2],
                reward_critical_success=self.roll[3],
                reward_critical_failure=self.roll[4],
            )

        return roll
    
    async def update_roll(self) -> None:
        '''
        Update the roll object.
        
        Parameters
        ----------
        roll : Roll
            The roll object to update.
        
        Returns
        -------
        None
        '''
    
        await self.connection.execute(
            """
            UPDATE roll SET
                status = ?,
                minimum_bet = ?,
                maximum_bet = ?,
                reward_critical_success = ?,
                reward_critical_failure = ?
        """,
            (
                self.roll.status,
                self.roll.minimum_bet,
                self.roll.maximum_bet,
                self.roll.reward_critical_success,
                self.roll.reward_critical_failure,
            ),
        )

        await self.connection.commit()
        self.logger.info("Roll updated.")
    
    async def update_slots(self) -> None:
        '''
        Update the slots object.
        
        Parameters
        ----------
        slots : Slots
            The slots object to update.
        
        Returns
        -------
        None
        '''

        self.slots = slots

        await self.connection.execute(
            """
            UPDATE slots SET
                cost = ?,
                status = ?,
                rng_manipulation = ?,
                success_rate = ?,
                reward_mushroom = ?,
                reward_coin = ?,
                reward_leaf = ?,
                reward_diamond = ?,
                jackpot = ?
        """,
            (
                self.slots.cost,
                self.slots.status,
                self.slots.rng_manipulation,
                self.slots.success_rate,
                self.slots.reward_mushroom,
                self.slots.reward_coin,
                self.slots.reward_leaf,
                self.slots.reward_diamond,
                self.slots.jackpot,
            ),
        )

        await self.connection.commit()
        self.logger.info("Slots updated.")