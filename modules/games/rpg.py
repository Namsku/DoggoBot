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
    success_rate: float
    success_bonus: int
    boss_bonus: int
    boss_malus: int


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


    def validate_field(self, field, field_name, min_val=None, max_val=None, is_digit=True, is_empty_allowed=False):
        if is_digit and not field.isdigit():
            return {"error": f"{field_name} must be a number"}

        if is_digit:
            field = int(field)

        if min_val is not None and field < min_val or max_val is not None and field > max_val:
            return {"error": f"{field_name} must be between {min_val} and {max_val}"}

        if not is_empty_allowed and field == "":
            return {"error": f"{field_name} must not be empty"}

        return None

    async def add_rpg_profile(self, rpg : Rpg):
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
        if isinstance(rpg, dict):
            rpg = Rpg(**rpg)

        if await self.is_name_exists(rpg.name):
            return {"error": "name already exists"}

        if not self.is_name_valid(rpg.name):
            return {"error": f"command {rpg.name} must only contains letters or/and numbers"}

        fields_to_validate = [
            (rpg.cost, "cost", 0, 1000000000),
            (rpg.success_rate, "success rate", 1, 100, False),
            (rpg.description, "description", is_empty_allowed=True),
            (rpg.success_bonus, "success bonus", 0, 1000000000),
            (rpg.boss_bonus, "boss bonus", 0, 1000000000),
            (rpg.boss_malus, "boss malus", 0, 1000000000)
        ]

        for field in fields_to_validate:
            error = self.validate_field(*field)
            if error:
                return error

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

        fields_to_validate = [
            (rpg.cost, "cost", 0, 1000000000),
            (rpg.success_rate, "success rate", 1, 100, False),
            (rpg.description, "description", is_empty_allowed=True),
            (rpg.success_bonus, "success bonus", 0, 1000000000),
            (rpg.boss_bonus, "boss bonus", 0, 1000000000),
            (rpg.boss_malus, "boss malus", 0, 1000000000)
        ]

        for field in fields_to_validate:
            error = self.validate_field(*field)
            if error:
                return error

        sql_query = f"UPDATE rpg SET {', '.join(f'{key} = :{key}' for key in rpg.keys())} WHERE id = :id"
        await self.connection.execute(sql_query, rpg)
        await self.connection.commit()

        return {"success": f"rpg profile {rpg.name} updated successfully"}