from modules.logger import Logger

from dataclasses import asdict, dataclass
import aiosqlite

from typing import Union


@dataclass
class Rpg:
    id: int
    name: str
    cost: int
    success_rate: int
    success_bonus: float
    boss_bonus: float
    boss_malus: float
    timer: int


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
        self.success_rate = None
        self.success_bonus = None
        self.boss_bonus = None
        self.boss_malus = None
        self.timer = None
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

        # if nothing on table ?


        async with self.connection.execute("SELECT id FROM rpg ORDER BY id DESC LIMIT 1") as cursor:
            last_id = await cursor.fetchone()

        return last_id[0] if last_id else 0

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

        if isinstance(rpg, str):
            rpg = Rpg(
                id = await self.get_last_id() + 1,
                name = rpg,
                cost = 1000,
                success_rate = 50,
                success_bonus = 100,
                boss_bonus = 7.777,
                boss_malus = 6.66,
                timer = 60
            )
    
        if isinstance(rpg, dict):
            rpg = Rpg(**rpg)

        if await self.is_name_exists(rpg.name):
            return {"error": "name already exists"}
        
        rpg = asdict(rpg)

        sql_query = f"INSERT INTO rpg ({', '.join(rpg.keys())}) VALUES ({', '.join(':' + key for key in rpg.keys())})"
        await self.connection.execute(sql_query, rpg)
        await self.connection.commit()

        return {"success": f"RPG profile {rpg['name']} added successfully"}

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
    
    async def get_rpg_profile_by_name(self, name: str) -> Rpg:
        """
        Get a rpg profile by name from the database.

        Parameters
        ----------
        name : str
            The name of the rpg profile.

        Returns
        -------
        Rpg
            The rpg profile.
        """
        sql_query = "SELECT * FROM rpg WHERE name = ?"
        async with self.connection.execute(sql_query, (name,)) as cursor:
            content = await cursor.fetchone()
            if content:
                return Rpg(*content)
            else:
                return None
            
    async def validate_form_content(self, form: dict) -> dict:
        """
        Validate the form content.

        Parameters
        ----------
        form : dict
            The form to validate.

        Returns
        -------
        dict
            The result.
        """
        fields = [
            ("rpg_cost", "The cost can't be empty", "The cost must be a number"),
            ("rpg_success_rate", "The success rate can't be empty", "The success rate must be a number"),
            ("rpg_success_bonus", "The success bonus can't be empty", "The success bonus must be a number"),
            ("rpg_boss_bonus", "The boss bonus can't be empty", "The boss bonus must be a number"),
            ("rpg_boss_malus", "The boss malus can't be empty", "The boss malus must be a number"),
            ("rpg_timer", "The timer can't be empty", "The timer must be a number")
        ]

        for field, empty_error, type_error in fields:
            value = form.get(field)
            if value is None:
                return {"error": empty_error}
            if field in [
                "rpg_cost",
                "rpg_success_rate",
                "rpg_success_bonus",
                "rpg_boss_bonus",
                "rpg_boss_malus",
                "rpg_timer"
            ]:
                if not value.replace(".", "").isdigit():
                    return {"error": type_error}
                else:
                    if not value.isdigit():
                        return {"error": type_error}
                    
        return None
    
    async def fill_cfg(self, form: dict) -> dict:
        return {
            "id": form.get("rpg_id"),
            "name": form.get("rpg_name"),
            "cost": form.get("rpg_cost"),
            "success_rate": form.get("rpg_success_rate"),
            "success_bonus": form.get("rpg_success_bonus"),
            "boss_bonus": form.get("rpg_boss_bonus"),
            "boss_malus": form.get("rpg_boss_malus"),
            "timer": form.get("rpg_timer")
        }
    
    async def set_rpg(self, form) -> dict:
        """
        Set a rpg profile.

        Parameters
        ----------
        form : dict
            The form to set.

        Returns
        -------
        dict
            The result.
        """

        error_form_invalid = await self.validate_form_content(form)
        if error_form_invalid:
            return error_form_invalid
        
        cfg = await self.fill_cfg(form)
        return await self.update_rpg_profile(cfg)