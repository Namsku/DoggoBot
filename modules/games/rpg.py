from collections import OrderedDict
from modules.logger import Logger
from twitchio.ext import commands

from dataclasses import asdict, dataclass
import aiosqlite

from typing import Union


@dataclass
class Rpg:
    id: int
    name: str
    cost: int
    win_rate: int
    win_bonus: float
    boss_bonus: float
    boss_malus: float
    timer: int
    ratio_normal_event: int
    ratio_treasure_event: int
    ratio_monster_event: int
    ratio_trap_event: int
    ratio_boss_event: int


@dataclass
class RpgEvent:
    id: int
    rpg_id: int
    message: str
    type: str
    event: str


class RpgCog(commands.Cog):
    def __init__(self, connection: aiosqlite.Connection) -> None:
        """
        Initializes the RpgCog class.

        Parameters
        ----------
        connection : aiosqlite.Connection
            The connection to the database.
        """
        self.connection = connection
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

        async with self.connection.execute(
            "SELECT id FROM rpg ORDER BY id DESC LIMIT 1"
        ) as cursor:
            last_id = await cursor.fetchone()

        return last_id[0] if last_id else 0

    async def add_rpg_profile(self, rpg: Union[Rpg, str] = None):
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
                id=await self.get_last_id() + 1,
                name=rpg,
                cost=1000,
                win_rate=50,
                win_bonus=100,
                boss_bonus=7.777,
                boss_malus=6.66,
                timer=60,
                ratio_normal_event=20,
                ratio_treasure_event=5,
                ratio_monster_event=60,
                ratio_trap_event=5,
                ratio_boss_event=10,
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

    async def update_rpg_profile(self, rpg: Rpg):
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

        # put all ratio into a integer variable
        rpg_ratio = sum(
            int(ratio)
            for ratio in [
                rpg.ratio_normal_event,
                rpg.ratio_treasure_event,
                rpg.ratio_monster_event,
                rpg.ratio_trap_event,
                rpg.ratio_boss_event,
            ]
        )
        ratio = 100 - rpg_ratio

        if ratio != 0:
            return {"error": "ratios must be equal to 100"}

        rpg = asdict(rpg)

        sql_query = f"UPDATE rpg SET {', '.join(f'{key} = :{key}' for key in rpg.keys())} WHERE id = :id"
        await self.connection.execute(sql_query, rpg)
        await self.connection.commit()

        return {"success": f"rpg profile {rpg['name']} updated successfully"}

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

    async def get_rpg_event_by_id(self, id: int) -> RpgEvent:
        """
        Get a rpg event by id from the database.

        Parameters
        ----------
        id : int
            The id of the rpg event.

        Returns
        -------
        RpgEvent
            The rpg event.
        """

        sql_query = "SELECT * FROM rpg_event WHERE id = ?"

        async with self.connection.execute(sql_query, (id,)) as cursor:
            content = await cursor.fetchone()
            if content:
                return RpgEvent(*content)
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
            (
                "rpg_win_rate",
                "The success rate can't be empty",
                "The success rate must be a number",
            ),
            (
                "rpg_win_bonus",
                "The success bonus can't be empty",
                "The success bonus must be a number",
            ),
            (
                "rpg_boss_bonus",
                "The boss bonus can't be empty",
                "The boss bonus must be a number",
            ),
            (
                "rpg_boss_malus",
                "The boss malus can't be empty",
                "The boss malus must be a number",
            ),
            ("rpg_timer", "The timer can't be empty", "The timer must be a number"),
            (
                "rpg_ratio_normal_event",
                "The ratio normal event can't be empty",
                "The ratio normal event must be a number",
            ),
            (
                "rpg_ratio_treasure_event",
                "The ratio treasure event can't be empty",
                "The ratio treasure event must be a number",
            ),
            (
                "rpg_ratio_monster_event",
                "The ratio monster event can't be empty",
                "The ratio monster event must be a number",
            ),
            (
                "rpg_ratio_trap_event",
                "The ratio trap event can't be empty",
                "The ratio trap event must be a number",
            ),
            (
                "rpg_ratio_boss_event",
                "The ratio boss event can't be empty",
                "The ratio boss event must be a number",
            ),
        ]

        for field, empty_error, type_error in fields:
            value = form.get(field)
            if value is None:
                return {"error": empty_error}
            if field in [
                "rpg_win_rate",
                "rpg_win_bonus",
                "rpg_boss_bonus",
                "rpg_boss_malus",
                "rpg_ratio_normal_event",
                "rpg_ratio_treasure_event",
                "rpg_ratio_monster_event",
                "rpg_ratio_trap_event",
                "rpg_ratio_boss_event",
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
            "win_rate": form.get("rpg_win_rate"),
            "win_bonus": form.get("rpg_win_bonus"),
            "boss_bonus": form.get("rpg_boss_bonus"),
            "boss_malus": form.get("rpg_boss_malus"),
            "timer": form.get("rpg_timer"),
            "ratio_normal_event": form.get("rpg_ratio_normal_event"),
            "ratio_treasure_event": form.get("rpg_ratio_treasure_event"),
            "ratio_monster_event": form.get("rpg_ratio_monster_event"),
            "ratio_trap_event": form.get("rpg_ratio_trap_event"),
            "ratio_boss_event": form.get("rpg_ratio_boss_event"),
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

    async def get_rpg_profile_id(self, name: str) -> int:
        """
        Get a rpg profile id by name from the database.

        Parameters
        ----------
        name : str
            The name of the rpg profile.

        Returns
        -------
        int
            The rpg profile id.
        """

        if isinstance(name, dict):
            name = name.get("name")

        sql_query = "SELECT id FROM rpg WHERE name = ?"
        async with self.connection.execute(sql_query, (name,)) as cursor:
            content = await cursor.fetchone()
            if content:
                return content[0]
            else:
                return None

    async def delete_rpg_profile(self, name: str) -> dict:
        """
        Delete a rpg profile from the database.

        Parameters
        ----------
        name : str
            The name of the rpg profile.

        Returns
        -------
        dict
            The result.
        """

        if isinstance(name, dict):
            name = name.get("name")

        if not await self.is_name_exists(name):
            return {"error": "name not exists"}

        sql_query = "DELETE FROM rpg WHERE name = ?"
        await self.connection.execute(sql_query, (name,))
        await self.connection.commit()

        return {"success": f"rpg profile {name} deleted successfully"}

    async def add_rpg_event(self, rpg_event: RpgEvent):
        """
        Adds a rpg event to the database.

        Parameters
        ----------
        rpg_event : RpgEvent
            The rpg event to add.

        Returns
        -------
        dict
            The result.
        """
        if isinstance(rpg_event, dict):
            ordered_dict = OrderedDict()
            ordered_dict["id"] = await self.get_last_event_id() + 1
            ordered_dict["rpg_id"] = rpg_event.get("rpg_id")
            ordered_dict["message"] = rpg_event.get("message")
            ordered_dict["type"] = rpg_event.get("type")
            ordered_dict["event"] = rpg_event.get("event")
            rpg_event = RpgEvent(**ordered_dict)

        rpg_event = asdict(rpg_event)

        sql_query = f"INSERT INTO rpg_event ({', '.join(rpg_event.keys())}) VALUES ({', '.join(':' + key for key in rpg_event.keys())})"
        await self.connection.execute(sql_query, rpg_event)
        await self.connection.commit()

        return {"success": f"RPG event {rpg_event['id']} added successfully"}

    async def update_rpg_event(self, rpg_event: RpgEvent):
        """
        Updates a rpg event in the database.

        Parameters
        ----------
        rpg_event : RpgEvent
            The rpg event to update.

        Returns
        -------
        dict
            The result.
        """

        if isinstance(rpg_event, RpgEvent):
            rpg_event = asdict(rpg_event)

        sql_query = f"UPDATE rpg_event SET {', '.join(f'{key} = :{key}' for key in rpg_event.keys())} WHERE id = :id"
        await self.connection.execute(sql_query, rpg_event)
        await self.connection.commit()

        return {"success": f"rpg event {rpg_event['id']} updated successfully"}

    async def delete_rpg_event_by_id(self, id: int):
        """
        Deletes a rpg event from the database.

        Parameters
        ----------
        id : int
            The id of the rpg event to delete.

        Returns
        -------
        dict
            The result.
        """

        if isinstance(id, dict):
            id = id.get("name")

        if isinstance(id, str):
            id = int(id)

        if isinstance(id, RpgEvent):
            id = id.id

        sql_query = "DELETE FROM rpg_event WHERE id = ?"
        await self.connection.execute(sql_query, (id,))
        await self.connection.commit()

        return {"success": f"rpg event {id} deleted successfully"}

    async def delete_all_rpg_events_by_id(self, rpg_id: int):
        """
        Deletes all rpg events by id from the database.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The result.
        """
        sql_query = "DELETE FROM rpg_event WHERE rpg_id = ?"
        await self.connection.execute(sql_query, (rpg_id,))
        await self.connection.commit()

        return {"success": f"all rpg events with rpg id {rpg_id} deleted successfully"}

    async def get_all_rpg_events_by_id(self, rpg_id: int):
        """
        Get all rpg events by id from the database.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        list
            The list of rpg events.
        """

        sql_query = "SELECT * FROM rpg_event WHERE rpg_id = ?"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return [RpgEvent(*event) for event in content]
            else:
                return {}

    async def fill_default_rpg_events(self, rpg_id: int):
        """
        Fill the default rpg events.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The result.
        """

        adventure_events = [
            ["You stumble upon a hidden chest.", "Treasure", "Win"],
            ["A group of goblins ambushes {user}.", "Monster", "Loss"],
            ["You decipher an ancient script.", "Normal", "Win"],
            ["A massive dragon confronts {user}.", "Boss", "Loss"],
            ["You trigger a hidden trap.", "Trap", "Loss"],
            ["You discover a pile of gold coins.", "Treasure", "Win"],
            ["A bandit attacks {user} unexpectedly.", "Monster", "Tie"],
            ["You uncover a magical amulet.", "Treasure", "Win"],
            ["A terrifying demon blocks {user}'s path.", "Boss", "Loss"],
            ["You solve a complex puzzle.", "Normal", "Win"],
            ["A hidden snare traps {user}.", "Trap", "Loss"],
            ["You find a chest filled with gems.", "Treasure", "Win"],
            ["A pack of wolves surrounds {user}.", "Monster", "Tie"],
            ["You acquire a legendary sword.", "Treasure", "Win"],
            ["A mighty ogre challenges {user} to a duel.", "Boss", "Loss"],
            ["You discover a hidden passage.", "Normal", "Win"],
            ["A pit trap catches {user} off guard.", "Trap", "Loss"],
            ["You unearth a trove of ancient artifacts.", "Treasure", "Win"],
            ["A horde of orcs ambushes {user}.", "Monster", "Loss"],
            ["You decipher an old map.", "Normal", "Win"],
            ["A poison dart narrowly misses {user}.", "Trap", "Win"],
            ["You find a chest filled with rare treasures.", "Treasure", "Win"],
            ["A fearsome troll blocks {user}'s way.", "Boss", "Loss"],
            ["You stumble upon an abandoned campsite.", "Normal", "Win"],
            ["A falling boulder narrowly misses {user}.", "Trap", "Win"],
            ["You unearth a valuable gemstone.", "Treasure", "Win"],
            ["A pack of wild boars charges at {user}.", "Monster", "Tie"],
            ["You decipher an ancient inscription.", "Normal", "Win"],
            ["A swinging pendulum narrowly misses {user}.", "Trap", "Win"],
            [
                "You discover a chest filled with precious jewels.",
                "Treasure",
                "Win",
            ],
            ["A powerful sorcerer appears before {user}.", "Boss", "Loss"],
            ["You uncover a hidden stash of gold.", "Treasure", "Win"],
            ["A swarm of spiders descends upon {user}.", "Monster", "Loss"],
            ["You navigate through a dark maze.", "Normal", "Win"],
            ["A trapdoor opens beneath {user}.", "Trap", "Loss"],
            ["You unearth a legendary artifact.", "Treasure", "Win"],
            ["A ferocious bear confronts {user}.", "Monster", "Tie"],
            ["You solve a challenging riddle.", "Normal", "Win"],
            ["A dart trap narrowly misses {user}.", "Trap", "Win"],
            ["You discover a chest of ancient relics.", "Treasure", "Win"],
            ["A menacing minotaur stands in {user}'s way.", "Boss", "Loss"],
            ["You find a hidden cave entrance.", "Normal", "Win"],
            ["A pressure plate triggers beneath {user}.", "Trap", "Loss"],
            ["You uncover a chest of enchanted treasures.", "Treasure", "Win"],
            ["A pack of hungry wolves surrounds {user}.", "Monster", "Tie"],
            ["You decipher a cryptic message.", "Normal", "Win"],
            ["A hidden arrow narrowly misses {user}.", "Trap", "Win"],
            ["You unearth a chest of magical artifacts.", "Treasure", "Win"],
            ["A fearsome wyvern swoops down upon {user}.", "Boss", "Loss"],
            ["You come across a tranquil village.", "Normal", "Win"],
        ]

        for event in adventure_events:
            # event is a list and need to be converted to a dict
            event = {
                "id": await self.get_last_event_id() + 1,
                "rpg_id": rpg_id,
                "message": event[0],
                "type": event[1],
                "event": event[2],
            }

            await self.add_rpg_event(RpgEvent(**event))

        return {"success": "default rpg events added successfully"}

    async def get_last_event_id(self) -> int:
        """
        Get the last event id from the database.

        Parameters
        ----------
        None

        Returns
        -------
        int
            The last event id.
        """
        async with self.connection.execute(
            "SELECT id FROM rpg_event ORDER BY id DESC LIMIT 1"
        ) as cursor:
            last_id = await cursor.fetchone()

        return last_id[0] if last_id else 0

    async def get_rpg_types_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg types stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg types stats.
            {
                "type1": count,
                "type2": count,
                "type3": count,
            }
        """

        sql_query = (
            "SELECT type, COUNT(*) FROM rpg_event WHERE rpg_id = ? GROUP BY type"
        )
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event_type: count for event_type, count in content}
            else:
                return {}

    async def get_rpg_actions_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg actions stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg actions stats.
            {
                "action1": count,
                "action2": count,
                "action3": count,
            }
        """

        sql_query = (
            "SELECT event, COUNT(*) FROM rpg_event WHERE rpg_id = ? GROUP BY event"
        )
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event: count for event, count in content}
            else:
                return {}

    async def get_rpg_normal_actions_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg normal actions stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg normal actions stats.
            {
                "action1": count,
                "action2": count,
                "action3": count,
            }
        """

        sql_query = "SELECT event, COUNT(*) FROM rpg_event WHERE rpg_id = ? AND type = 'Normal' GROUP BY event"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event: count for event, count in content}
            else:
                return {}

    async def get_rpg_treasure_actions_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg treasure actions stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg treasure actions stats.
            {
                "action1": count,
                "action2": count,
                "action3": count,
            }
        """

        sql_query = "SELECT event, COUNT(*) FROM rpg_event WHERE rpg_id = ? AND type = 'Treasure' GROUP BY event"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event: count for event, count in content}
            else:
                return {}

    async def get_rpg_monster_actions_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg monster actions stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg monster actions stats.
            {
                "action1": count,
                "action2": count,
                "action3": count,
            }
        """

        sql_query = "SELECT event, COUNT(*) FROM rpg_event WHERE rpg_id = ? AND type = 'Monster' GROUP BY event"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event: count for event, count in content}
            else:
                return {}

    async def get_rpg_trap_actions_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg trap actions stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg trap actions stats.
            {
                "action1": count,
                "action2": count,
                "action3": count,
            }
        """

        sql_query = "SELECT event, COUNT(*) FROM rpg_event WHERE rpg_id = ? AND type = 'Trap' GROUP BY event"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event: count for event, count in content}
            else:
                return {}

    async def get_rpg_boss_actions_stats(self, rpg_id: int) -> dict:
        """
        Get the rpg boss actions stats.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        dict
            The rpg boss actions stats.
            {
                "action1": count,
                "action2": count,
                "action3": count,
            }
        """

        sql_query = "SELECT event, COUNT(*) FROM rpg_event WHERE rpg_id = ? AND type = 'Boss' GROUP BY event"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchall()
            if content:
                return {event: count for event, count in content}
            else:
                return {}

    async def get_random_event(self, rpg_list) -> RpgEvent:
        """
        Get a random event.

        Parameters
        ----------
        rpg_id : int
            The id of the rpg.

        Returns
        -------
        RpgEvent
            The random event.
        """

        sql_query = "SELECT * FROM rpg_event WHERE rpg_id = ? ORDER BY RANDOM() LIMIT 1"
        async with self.connection.execute(sql_query, (rpg_id,)) as cursor:
            content = await cursor.fetchone()
            if content:
                return RpgEvent(*content)
            else:
                return None

    async def start_game(self) -> list:
            """
            Get all rpg events by active groups from the database.

            Parameters
            ----------
            active_groups : list
                The active groups.

            Returns
            -------
            list
                The list of rpg events.
            """

            # Get all ID from active games from Games table
            sql_query = "SELECT id FROM games WHERE active = 1"
            async with self.connection.execute(sql_query) as cursor:
                active_games = await cursor.fetchall()

            # Get all events from active games in their respective list
            events = []
            for game in active_games:
                sql_query = "SELECT * FROM rpg_event WHERE rpg_id = ?"
                async with self.connection.execute(sql_query, (game[0],)) as cursor:
                    content = await cursor.fetchall()
                    if content:
                        events.append(content)
                    else:
                        events.append({})

            print(events)
            
            return events
