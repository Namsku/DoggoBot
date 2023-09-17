import aiosqlite

from twitchio.ext import sounds, commands
from dataclasses import dataclass

@dataclass
class curse:
    id: int
    name: str
    path: str
    volume: int
    cost: int
    cooldown: int

class curseCog():
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection
        self.player = sounds.AudioPlayer(callback=self.sound_executed)
        self.source = None

    async def create_table(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS curse (
                id INTEGER PRIMARY KEY,
                name TEXT,
                path TEXT,
                volume INTEGER,
                cost INTEGER,
                cooldown INTEGER
            )
        """
        )

        await self.connection.commit()

    async def user_able_to_play(self, ctx: commands.Context, curse_sound: str) -> bool:
        '''
        Checks if a user is able to play a sound effect.

        Parameters
        ----------
        ctx : commands.Context
            The context of the command.
        curse_sound : str
            The name of the sound effect.

        Returns
        -------
        bool
            Whether or not the user is able to play the sound effect.
        '''

        curse = await self.get_curse(curse_sound)

        if curse is None:
            return False

        user = await self.get_user(ctx.author.name)

        if user is None:
            return False

        if user.coins < curse.cost:
            ctx.channel.send(f"{ctx.author.name} does not have enough {self.coin_name} to play {curse.name}.")
            return False

        if user.curse_lock > 0:
            ctx.channel.send(f"{ctx.author.name} is on cooldown for {user.curse_lock} seconds.")
            return False

        return True

    async def play_curse(self, ctx: commands.Context, curse_sound: str) -> None:
        '''
        Plays a sound effect.

        Parameters
        ----------
        ctx : commands.Context
            The context of the command.
        curse_sound : str
            The name of the sound effect.

        Returns
        -------
        None
        '''
        
        event_player = sounds.AudioPlayer(callback=self.sound_done)
        curse = await self.get_curse(curse_sound)

        if curse is None:
            return
        
        event_player.source = self.source
        await event_player.play(curse.path, volume=curse.volume)

    async def get_curse(self, name: str) -> curse:
        async with self.connection.execute(
            """
            SELECT * FROM curse WHERE name = ?
        """,
            (name,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return curse(*result)
    
    async def get_curse_by_id(self, id: int) -> curse:
        async with self.connection.execute(
            """
            SELECT * FROM curse WHERE id = ?
        """,
            (id,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return curse(*result)
    
    async def get_all_curse(self) -> list[curse]:
        async with self.connection.execute(
            """
            SELECT * FROM curse
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [curse(*curse) for curse in result]
    
    async def get_all_curse_names(self) -> list[str]:
        async with self.connection.execute(
            """
            SELECT name FROM curse
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [name[0] for name in result]
    
    async def get_all_curse_paths(self) -> list[str]:
        async with self.connection.execute(
            """
            SELECT path FROM curse
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [path[0] for path in result]
    
    async def get_all_curse_volumes(self) -> list[int]:
        async with self.connection.execute(
            """
            SELECT volume FROM curse
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [volume[0] for volume in result]
    
    async def get_all_curse_costs(self) -> list[int]:
        async with self.connection.execute(
            """
            SELECT cost FROM curse
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [cost[0] for cost in result]
    
    async def get_all_curse_cooldowns(self) -> list[int]:
        async with self.connection.execute(
            """
            SELECT cooldown FROM curse
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [cooldown[0] for cooldown in result]
    
    async def add_curse(self, name: str, path: str, volume: int, cost: int, cooldown: int) -> None:
        await self.connection.execute(
            """
            INSERT INTO curse (name, path, volume, cost, cooldown) VALUES (?, ?, ?, ?, ?)
        """,
            (name, path, volume, cost, cooldown),
        )
        await self.connection.commit()
    
    async def delete_curse(self, name: str) -> None:
        await self.connection.execute(
            """
            DELETE FROM curse WHERE name = ?
        """,
            (name,),
        )
        await self.connection.commit()

    async def update_curse(self, name: str, path: str, volume: int, cost: int, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET path = ?, volume = ?, cost = ?, cooldown = ? WHERE name = ?
        """,
            (path, volume, cost, cooldown, name),
        )
        await self.connection.commit()

    async def update_curse_path(self, name: str, path: str) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET path = ? WHERE name = ?
        """,
            (path, name),
        )
        await self.connection.commit()

    async def update_curse_volume(self, name: str, volume: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET volume = ? WHERE name = ?
        """,
            (volume, name),
        )
        await self.connection.commit()
    
    async def update_curse_cost(self, name: str, cost: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET cost = ? WHERE name = ?
        """,
            (cost, name),
        )
        await self.connection.commit()
    
    async def update_curse_cooldown(self, name: str, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET cooldown = ? WHERE name = ?
        """,
            (cooldown, name),
        )
        await self.connection.commit()
    
    async def update_curse_volume_by_id(self, id: int, volume: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET volume = ? WHERE id = ?
        """,
            (volume, id),
        )
        await self.connection.commit()
    
    async def update_curse_cost_by_id(self, id: int, cost: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET cost = ? WHERE id = ?
        """,
            (cost, id),
        )
        await self.connection.commit()
    
    async def update_curse_cooldown_by_id(self, id: int, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET cooldown = ? WHERE id = ?
        """,
            (cooldown, id),
        )
        await self.connection.commit()
    
    async def update_curse_path_by_id(self, id: int, path: str) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET path = ? WHERE id = ?
        """,
            (path, id),
        )
        await self.connection.commit()
    
    async def update_curse_name_by_id(self, id: int, name: str) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET name = ? WHERE id = ?
        """,
            (name, id),
        )
        await self.connection.commit()
    
    async def update_curse_name(self, old_name: str, new_name: str) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET name = ? WHERE name = ?
        """,
            (new_name, old_name),
        )
        await self.connection.commit()
    
    async def update_curse_path_by_name(self, old_name: str, new_path: str) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET path = ? WHERE name = ?
        """,
            (new_path, old_name),
        )
        await self.connection.commit()
    
    async def update_curse_volume_by_name(self, name: str, volume: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET volume = ? WHERE name = ?
        """,
            (volume, name),
        )
        await self.connection.commit()
    
    async def update_curse_cost_by_name(self, name: str, cost: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET cost = ? WHERE name = ?
        """,
            (cost, name),
        )
        await self.connection.commit()
    
    async def update_curse_cooldown_by_name(self, name: str, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE curse SET cooldown = ? WHERE name = ?
        """,
            (cooldown, name),
        )
        await self.connection.commit()
    
    

    
