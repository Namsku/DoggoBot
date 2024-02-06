from collections import OrderedDict
from modules.logger import Logger
from modules.games.gambling import GamblingCog
from modules.games.rpg import RpgCog

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
        
        self.rpg = RpgCog(connection)
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
                name TEXT NOT NULL,
                cost INTEGER NOT NULL,
                success_rate REAL NOT NULL,
                success_bonus INTEGER NOT NULL,
                boss_bonus INTEGER NOT NULL,
                boss_malus INTEGER NOT NULL,
                timer INTEGER NOT NULL
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

        if isinstance(game, dict):
            if 'id' not in game:
                ordered_game = OrderedDict()
                ordered_game['id'] = await self.get_last_id()
                ordered_game['name'] = game['name']
                ordered_game['category'] = game['category']
                ordered_game['description'] = game['description']
                ordered_game['status'] = game['status']
                game = dict(ordered_game)

        if game['name'] is None:
            return {"error": "name is required"}
        
        if game['name'] == "":
            return {"error": "name cannot be empty"}
        
        if game['name'] in [game['name'] for game in await self.get_all_games()]:
            return {"error": "name already exists"}
        
        # game name must be alphanumeric with no spaces
        if not game['name'].isalnum():
            return {"error": "name must be alphanumeric"}

        if game['category'] is None:
            return {"error": "category is required"}
        
        if game['category'] not in ['RPG', 'Gatcha']:
            return {"error": "category must be RPG or Gatcha"}
        
        if game['status'] is None:
            return {"error": "status is required"}
        
        if game['status'] not in ["0", "1"]:
            return {"error": "status must be 0 or 1"}
        
        if game['description'] is None:
            return {"error": "description is required"}
        
        if game['description'] == "":
            return {"error": "description cannot be empty"}

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
        self.logger.info(f"Updated game status -> {game_name} -> {status}.")
        return {"success": f"game {game_name} updated successfully"}
    
    async def get_last_id(self) -> int:
        """
        Get the last game id from the database.

        Parameters
        ----------
        None

        Returns
        -------
        int
            The last game id.
        """

        async with self.connection.execute("SELECT id FROM game ORDER BY id DESC LIMIT 1") as cursor:
            last_id = await cursor.fetchone()

        return last_id[0] if last_id else 0