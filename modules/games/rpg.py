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

    async def add_rpg_profile(self, rpg: Union[Rpg, dict]) -> dict:
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

        # Quit if the name already exists
        if await self.is_cmd_exists(rpg.name):
            return {"error": "name already exists"}

        if not self.is_name_valid(rpg.name):
            return {"error": f"command {rpg.name} must only contains letters or/and numbers"}

        if rpg.cost.isdigit() is False:
            return {"error": "cost must be a number"}

        rpg.cost = int(rpg.cost)
        if rpg.cost < 0 or rpg.cost > 1000000000:
            return {"error": "cost must be between 0 and 1 000 000 000"}

        if rpg.success_rate.isdigit() is False:
            return {"error": "cost must be a number"}

        rpg.success_rate = float(rpg.success_rate)
        if rpg.success_rate < 0 or rpg.success_rate > 100:
            return {"error": "cost must be between 0 and 100"}

        rpg.cost = int(rpg.cost)
        if rpg.cost < 0 or rpg.cost > 1000000000:
            return {"error": "cost must be between 0 and 1 000 000 000"}

        if rpg.success_rate.isdigit() is False:
            return {"error": "cost must be a number"}

        if rpg.description == "":
            return {"error": "description must not be empty"}

        await self.connection.execute(
            """
            INSERT INTO rpg (
                id,
                name,
                cost,
                description,
                success_rate,
                success_bonus,
                boss_bonus,
                boss_malus
            ) VALUES (
                :id,
                :name,
                :cost,
                :description,
                :success_rate,
                :success_bonus,
                :boss_bonus,
                :boss_malus
            )
            """,
            rpg,
        )

        await self.connection.commit()

        return rpg
