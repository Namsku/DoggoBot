from dataclasses import dataclass
from modules.logger import Logger
from modules.games.gambling import GamblingCog


import aiosqlite
import random
import time

@dataclass
class Game:
    id: int
    name: str
    type: str
    cost: int


class GamesCog:
    def __init__(self, connection: aiosqlite.Connection):
        """
        Initialize the GamesCog class.

        Parameters
        ----------
        connection : aiosqlite.Connection
            Connection to the database.

        Returns
        -------
        None
        """

        self.connection = connection
        self.logger = Logger(__name__)
        self.gambling = GamblingCog(connection)   

    async def __ainit__(self) -> None:
        """
        Initialize the GamesCog class.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.logger.info("Initializing GamesCog...")

    async def create_table(self):
        """
        Create the games table for rolls and slots.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

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
                jackpot INTEGER NOT NULL,
                time INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roll (
                status INTEGER NOT NULL,
                minimum_bet INTEGER NOT NULL,
                maximum_bet INTEGER NOT NULL,
                reward_critical_success REAL NOT NULL,
                reward_critical_failure REAL NOT NULL,
                time INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS game (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                cost INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rpg (
                id INTEGER PRIMARY KEY,
                name TEXT,
                cost INTEGER,
                description TEXT,
                success_rate REAL,
                success_bonus INTEGER,
                boss_bonus INTEGER,
                boss_malus INTEGER
            );

            CREATE TABLE IF NOT EXISTS rpg_action (
                id INTEGER PRIMARY KEY,
                rpg_id INTEGER,
                message TEXT,
                type TEXT,
                boss BOOLEAN,
                FOREIGN KEY(rpg_id) REFERENCES rpg(id)
            );            

            CREATE TABLE IF NOT EXISTS gatcha (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                rarity INTEGER NOT NULL,
                time INTEGER NOT NULL
            );
        """
        )    
    