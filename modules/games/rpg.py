from modules.logger import Logger

from dataclasses import dataclass
import aiosqlite

from typing import Union


@dataclass
class Rpg:
    id: int
    name: str
    cost: int
    description: str
    success_rate: int
    success_bonus: float
    boss_bonus: float
    boss_malus: float


class RpgCog:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        """
        Initializes the RpgCog class.

        Parameters
        ----------
        connection : aiosqlite.Connection
            The connection to the database.
        """
        self.connection = connection

        self.id = None
        self.name = None
        self.cost = None
        self.description = None
        self.success_rate = None
        self.success_bonus = None
        self.boss_bonus = None
        self.boss_malus = None
        self.logger = Logger(__name__)

    async def is_id_exists(self, id: int) -> bool:
        """
        Checks if the id exists in the database.

        Parameters
        ----------
        id : int
            The id to check.

        Returns
        -------
        bool
            True if the id exists, False otherwise.
        """
        sql_query = "SELECT * FROM rpg WHERE id = ?"
        async with self.connection.execute(sql_query, (id,)) as cursor:
            return await cursor.fetchone() is not None
    
    async def is_name_exists(self, name: str) -> bool:
        """
        Checks if the name exists in the database.

        Parameters
        ----------
        name : str
            The name to check.

        Returns
        -------
        bool
            True if the name exists, False otherwise.
        """
        sql_query = "SELECT * FROM rpg WHERE name = ?"
        async with self.connection.execute(sql_query, (name,)) as cursor:
            return await cursor.fetchone() is not None
        
    async def get_last_id(self) -> int:
        """
        Get the last id from the database.

        Parameters
        ----------
        None

        Returns
        -------
        int
            The last id.
        """
        async with self.connection.execute("SELECT id FROM rpg ORDER BY id DESC LIMIT 1") as cursor:
            return await cursor.fetchone()

    async def add_rpg_profile(self, rpg : Union[Rpg, str]  = None):
        """
        Adds a rpg profile to the database.

        Parameters
        ----------
        rpg : Union[Rpg, dict]
            The rpg profile to add.

        Returns
        -------
        rpg : dict
            The rpg profile.
        """

        if rpg is str:
            rpg = Rpg(
                id = await self.get_last_id() + 1,
                name = rpg,
                cost = 1000,
                success_rate = 50,
                success_bonus = 100,
                boss_bonus = 7.777,
                boss_malus = 6.66
            )
    
        if isinstance(rpg, dict):
            rpg = Rpg(**rpg)

        if await self.is_name_exists(rpg.name):
            return {"error": "name already exists"}

        sql_query = f"INSERT INTO rpg ({', '.join(rpg.keys())}) VALUES ({', '.join(':' + key for key in rpg.keys())})"
        await self.connection.execute(sql_query, rpg)
        await self.connection.commit()

        return {"success": f"rpg profile {rpg.name} added successfully"}

    async def update_rpg_profile(self, rpg : Rpg):
        """
        Updates a rpg profile in the database.

        Parameters
        ----------
        rpg : Union[Rpg, dict]
            The rpg profile to update.

        Returns
        -------
        rpg : dict
            The rpg profile.
        """
        if isinstance(rpg, dict):
            rpg = Rpg(**rpg)

        if not await self.is_id_exists(rpg.id):
            return {"error": "id not exists"}

        sql_query = f"UPDATE rpg SET {', '.join(f'{key} = :{key}' for key in rpg.keys())} WHERE id = :id"
        await self.connection.execute(sql_query, rpg)
        await self.connection.commit()

        return {"success": f"rpg profile {rpg.name} updated successfully"}