import aiosqlite

from twitchio.ext import sounds, commands
from dataclasses import dataclass

@dataclass
class SFX:
    id: int
    name: str
    path: str
    volume: int
    cost: int
    cooldown: int

class SFXCog():
    def __init__(self, connection: aiosqlite.Connection):
        '''
        Initializes the SFXCog class.
        
        Parameters
        ----------
        connection : aiosqlite.Connection
            The connection to the database.
        
        Returns
        -------
        None
        '''

        self.connection = connection
        self.source = None

    async def create_table(self):
        '''
        Creates the table for the database.

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''

        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sfx (
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

    async def user_able_to_play(self, ctx: commands.Context, sfx_sound: str) -> bool:
        '''
        Checks if a user is able to play a sound effect.

        Parameters
        ----------
        ctx : commands.Context
            The context of the command.
        sfx_sound : str
            The name of the sound effect.

        Returns
        -------
        bool
            Whether or not the user is able to play the sound effect.
        '''

        sfx = await self.get_sfx(sfx_sound)

        if sfx is None:
            return False

        user = await self.get_user(ctx.author.name)

        if user is None:
            return False

        if user.coins < sfx.cost:
            ctx.channel.send(f"{ctx.author.name} does not have enough {self.coin_name} to play {sfx.name}.")
            return False

        if user.sfx_lock > 0:
            ctx.channel.send(f"{ctx.author.name} is on cooldown for {user.sfx_lock} seconds.")
            return False

        return True

    async def play_sfx(self, ctx: commands.Context, sfx_sound: str) -> None:
        '''
        Plays a sound effect.

        Parameters
        ----------
        ctx : commands.Context
            The context of the command.
        sfx_sound : str
            The name of the sound effect.

        Returns
        -------
        None
        '''
        
        event_player = sounds.AudioPlayer(callback=self.sound_done)
        sfx = await self.get_sfx(sfx_sound)

        if sfx is None:
            return
        
        event_player.source = self.source
        await event_player.play(sfx.path, volume=sfx.volume)

    async def get_sfx(self, name: str) -> SFX:
        '''
        Gets a sound effect from the database.
        
        Parameters
        ----------
        name : str
            The name of the sound effect.
        
        Returns
        -------
        SFX
        '''

        async with self.connection.execute(
            """
            SELECT * FROM sfx WHERE name = ?
        """,
            (name,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return SFX(*result)
    
    async def get_sfx_by_id(self, id: int) -> SFX:
        '''
        Gets a sound effect from the database.
        
        Parameters
        ----------
        id : int
            The id of the sound effect.
        
        Returns
        -------
        SFX
        '''
        
        async with self.connection.execute(
            """
            SELECT * FROM sfx WHERE id = ?
        """,
            (id,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return SFX(*result)
    
    async def get_all_sfx(self) -> list[SFX]:
        '''
        Gets all sound effects from the database.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        list[SFX]
        '''
        
        async with self.connection.execute(
            """
            SELECT * FROM sfx
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [SFX(*sfx) for sfx in result]
    
    async def get_all_sfx_names(self) -> list[str]:
        async with self.connection.execute(
            """
            SELECT name FROM sfx
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [name[0] for name in result]
    
    async def get_all_sfx_paths(self) -> list[str]:
        async with self.connection.execute(
            """
            SELECT path FROM sfx
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [path[0] for path in result]
    
    async def get_all_sfx_volumes(self) -> list[int]:
        async with self.connection.execute(
            """
            SELECT volume FROM sfx
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [volume[0] for volume in result]
    
    async def get_all_sfx_costs(self) -> list[int]:
        async with self.connection.execute(
            """
            SELECT cost FROM sfx
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [cost[0] for cost in result]
    
    async def get_all_sfx_cooldowns(self) -> list[int]:
        async with self.connection.execute(
            """
            SELECT cooldown FROM sfx
        """
        ) as cursor:
            result = await cursor.fetchall()

        if result is None:
            return None

        return [cooldown[0] for cooldown in result]
    
    async def add_sfx(self, name: str, path: str, volume: int, cost: int, cooldown: int) -> None:
        await self.connection.execute(
            """
            INSERT INTO sfx (name, path, volume, cost, cooldown) VALUES (?, ?, ?, ?, ?)
        """,
            (name, path, volume, cost, cooldown),
        )
        await self.connection.commit()
    
    async def delete_sfx(self, name: str) -> None:
        await self.connection.execute(
            """
            DELETE FROM sfx WHERE name = ?
        """,
            (name,),
        )
        await self.connection.commit()

    async def update_sfx(self, name: str, path: str, volume: int, cost: int, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET path = ?, volume = ?, cost = ?, cooldown = ? WHERE name = ?
        """,
            (path, volume, cost, cooldown, name),
        )
        await self.connection.commit()

    async def update_sfx_path(self, name: str, path: str) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET path = ? WHERE name = ?
        """,
            (path, name),
        )
        await self.connection.commit()

    async def update_sfx_volume(self, name: str, volume: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET volume = ? WHERE name = ?
        """,
            (volume, name),
        )
        await self.connection.commit()
    
    async def update_sfx_cost(self, name: str, cost: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET cost = ? WHERE name = ?
        """,
            (cost, name),
        )
        await self.connection.commit()
    
    async def update_sfx_cooldown(self, name: str, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET cooldown = ? WHERE name = ?
        """,
            (cooldown, name),
        )
        await self.connection.commit()
    
    async def update_sfx_volume_by_id(self, id: int, volume: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET volume = ? WHERE id = ?
        """,
            (volume, id),
        )
        await self.connection.commit()
    
    async def update_sfx_cost_by_id(self, id: int, cost: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET cost = ? WHERE id = ?
        """,
            (cost, id),
        )
        await self.connection.commit()
    
    async def update_sfx_cooldown_by_id(self, id: int, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET cooldown = ? WHERE id = ?
        """,
            (cooldown, id),
        )
        await self.connection.commit()
    
    async def update_sfx_path_by_id(self, id: int, path: str) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET path = ? WHERE id = ?
        """,
            (path, id),
        )
        await self.connection.commit()
    
    async def update_sfx_name_by_id(self, id: int, name: str) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET name = ? WHERE id = ?
        """,
            (name, id),
        )
        await self.connection.commit()
    
    async def update_sfx_name(self, old_name: str, new_name: str) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET name = ? WHERE name = ?
        """,
            (new_name, old_name),
        )
        await self.connection.commit()
    
    async def update_sfx_path_by_name(self, old_name: str, new_path: str) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET path = ? WHERE name = ?
        """,
            (new_path, old_name),
        )
        await self.connection.commit()
    
    async def update_sfx_volume_by_name(self, name: str, volume: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET volume = ? WHERE name = ?
        """,
            (volume, name),
        )
        await self.connection.commit()
    
    async def update_sfx_cost_by_name(self, name: str, cost: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET cost = ? WHERE name = ?
        """,
            (cost, name),
        )
        await self.connection.commit()
    
    async def update_sfx_cooldown_by_name(self, name: str, cooldown: int) -> None:
        await self.connection.execute(
            """
            UPDATE sfx SET cooldown = ? WHERE name = ?
        """,
            (cooldown, name),
        )
        await self.connection.commit()
    
    

    
