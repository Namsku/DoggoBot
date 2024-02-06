from modules.logger import Logger
from modules.games.gambling import GamblingCog

from dataclasses import asdict, dataclass, fields
from typing import Union


import aiosqlite

@dataclass
class Game:
    id: int
    name: str
    category: str
    description: str
    status: int


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

        # create two table in one single execute
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
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                status INTEGER NOT NULL
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
                cost INTEGER NOT NULL,
                text TEXT NOT NULL,
                rarity INTEGER NOT NULL,
                time INTEGER NOT NULL
            );
        """
        )

        await self.connection.commit()
    
    async def add_game(self, game: Union[Game, dict]):
        """
        Add a game to the database.

        Parameters
        ----------
        game : Game
            The game to add.

        Returns
        -------
        None
        """


        if isinstance(game, Game):
            game = asdict(game)

        game_attributes = [field.name for field in fields(Game)]
        sql_request = f"INSERT INTO game ({', '.join(game_attributes)}) VALUES ({', '.join(':' + attribute for attribute in game_attributes)})"
        parameters = tuple(game.values())

        await self.connection.execute(sql_request, parameters)
        await self.connection.commit()

        return {"success": f"game {game['name']} added successfully"}
    
    async def update_game(self, game: Union[Game, dict]):
        """
        Update a game in the database.

        Parameters
        ----------
        game : Union[Game, dict]
            The game to update.

        Returns
        -------
        None
        """

        if isinstance(game, Game):
            game = asdict(game)

        sql_query = f"UPDATE game SET {', '.join(f'{key} = ?' for key in game.keys())} WHERE id = ?"
        parameters = tuple(list(game.values()) + [game["id"]])

        print(sql_query, parameters)

        await self.connection.execute(sql_query, parameters)
        await self.connection.commit()

        return {"success": f"game {game['name']} updated successfully"}

    async def delete_game_by_id(self, game_id: int):
        """
        Delete a game from the database.

        Parameters
        ----------
        game_id : int
            The game id to delete.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "DELETE FROM game WHERE id = ?",
            (game_id,)
        )

        await self.connection.commit()

        return {"success": f"game {game_id} deleted successfully"}
    
    async def delete_game_by_name(self, game_name: str):
        """
        Delete a game from the database.

        Parameters
        ----------
        game_name : str
            The game name to delete.

        Returns
        -------
        None
        """

        await self.connection.execute(
            "DELETE FROM game WHERE name = ?",
            (game_name,)
        )

        await self.connection.commit()
        self.logger.info(f"Deleted game -> {game_name}.")

        return {"success": f"game {game_name} deleted successfully"}

    async def get_all_games(self) -> list:
        """
        Get all games from the database.

        Parameters
        ----------
        None

        Returns
        -------
        list
            A list of all games.
        """

        async with self.connection.execute("SELECT * FROM game") as cursor:
            games = await cursor.fetchall()

        # Convert as list asdict(Game)
        games = [asdict(Game(*game)) for game in games]

        return games
    
    async def update_status(self, game_name: str, status: bool):
        """
        Get the game status from the database.

        Parameters
        ----------
        game_name : str
            The game name to update.

        status : int
            The game status to update.

        Returns
        -------
        None
        """

        status = 1 if status else 0

        await self.connection.execute("UPDATE game SET status = ? WHERE name = ?", (status, game_name))

        await self.connection.commit()
        self.logger.info(f"Updated cmd status -> {game_name} -> {status}.")
        return {"success": f"game {game_name} updated successfully"}