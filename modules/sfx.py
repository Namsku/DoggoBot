import hashlib
import zipfile
import aiosqlite

from pathlib import Path
from contextlib import closing
from dataclasses import asdict, dataclass

from twitchio.ext import sounds, commands

from modules.logger import Logger

@dataclass
class SFXEvent:
    id: int
    group_id: int
    sfx_id: int
    name: str
    path: str
    volume: int
    cost: int
    cooldown: int
    soundcard: str

class SFX:
    id: int
    group_id: int
    name: str
    volume: int
    cost: int
    cooldown: int
    soundcard: str

@dataclass
class SFXGroup:
    id: int
    name: str
    category: str
    description: str
    status: bool

class SFXCog(commands.Cog):
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection
        self.logger = Logger(__name__)
        self.sfx = {}
        # self.load_sfx()

        # init the sounds extension
        self.player = sounds.AudioPlayer(callback=self.reset_player)

    async def create_table(self):
        await self.connection.execute(
            """
                CREATE TABLE IF NOT EXISTS sfx_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status INTEGER NOT NULL
                )
            """
        )
        await self.connection.commit()

        await self.connection.execute(
            """
                CREATE TABLE IF NOT EXISTS sfx (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    name TEXT NOT NULL,
                    volume INTEGER NOT NULL,
                    cost INTEGER NOT NULL,
                    cooldown INTEGER NOT NULL,
                    soundcard TEXT NOT NULL,
                    FOREIGN KEY(group_id) REFERENCES sfx_groups(id)
                )
            """
        )
        await self.connection.commit()

        await self.connection.execute(
            """
                CREATE TABLE IF NOT EXISTS sfx_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    volume INTEGER NOT NULL,
                    cost INTEGER NOT NULL,
                    cooldown INTEGER NOT NULL,
                    soundcard TEXT NOT NULL,
                    group_id INTEGER,
                    sfx_id INTEGER,
                    FOREIGN KEY(group_id) REFERENCES sfx_groups(id)
                    FOREIGN KEY(sfx_id) REFERENCES sfx(id)
                )
            """
        )
        await self.connection.commit()
    
    def fill_default_sfx(self, group_id: int):
        sfx = [
            {
                "name": "default",
                "volume": 50,
                "cost": 0,
                "cooldown": 0,
                "soundcard": self.player.active_device,
                "group_id": group_id,
            }
        ]
        for s in sfx:
            self.add_sfx(s)

    def add_sfx_command(self, sfx: SFX):
        super().add_command(self.play_sfx, name=sfx.name, aliases=[sfx.name.lower()])

    def remove_sfx_command(self, sfx: SFX):
        super().remove_command(sfx.name)

    async def load_sfx(self):
        query = "SELECT * FROM sfx"
        async with self.connection.cursor() as cursor:
            sfx = await cursor.execute(query)
            for s in sfx:
                self.sfx[s[0]] = SFX(*s)

    async def reset_player(self):
        self.player.volume = 100
        self.player.stop()

    async def hash_file(self, filepath):
        """Return the MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def copy_sfx_files(self, source_folder, dest_folder=Path("data/sfx")):
        """Copy sound files from source_folder to dest_folder, renaming them to their SHA256 hash."""
        dest_folder.mkdir(parents=True, exist_ok=True)

        for source_path in source_folder.glob("*.[mM][pP]3") + source_folder.glob(
            "*.[wW][aA][vV]"
        ):
            hash_name = await self.hash_file(source_path)
            dest_path = dest_folder / (hash_name + source_path.suffix)

            if dest_path.exists():
                continue

            dest_path.write_bytes(source_path.read_bytes())

            # Add entry to SQL table
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO sfx (name, path, volume, cost, cooldown) VALUES (?, ?, ?, ?, ?)",
                    (source_path.name, str(dest_path), 100, 1000, 10),
                )
                await self.connection.commit()

    async def export_sfx_full_config(self, dest_folder=Path("data/sfx")):
        # Copy sound files from source_folder to dest_folder, renaming them to their SHA256 hash
        await self.copy_sfx_files(Path("data/sfx"), dest_folder)

        # Create a zip file to store the exported data
        zip_file_path = dest_folder / "sfx_export.zip"
        with closing(zipfile.ZipFile(zip_file_path, "w")) as zip_file:
            # Add the sound files to the zip file
            for sound_file in dest_folder.glob("*"):
                zip_file.write(sound_file, arcname=sound_file.name)

            # Add the SQL table to the zip file
            query = "SELECT * FROM sfx"
            async with self.connection.cursor() as cursor:
                sfx = await cursor.execute(query)
                table_data = "\n".join([",".join(map(str, s)) for s in sfx])
                zip_file.writestr("sfx_table.csv", table_data)

        return zip_file_path

    async def import_sfx_full_config(self, zip_file_path):
        # Erase the current profile
        await self.connection.execute("DELETE FROM sfx")
        await self.connection.commit()

        # Extract the zip file
        with closing(zipfile.ZipFile(zip_file_path, "r")) as zip_file:
            # Extract the sound files
            zip_file.extractall("data/sfx")

            # Read the SQL table data from the zip file
            table_data = zip_file.read("sfx_table.csv").decode("utf-8")

        # Insert the SQL table data into the database
        async with self.connection.cursor() as cursor:
            for line in table_data.split("\n"):
                if line:
                    values = line.split(",")
                    await cursor.execute(
                        "INSERT INTO sfx (name, path, volume, cost, cooldown, soundcard) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            values[1],
                            values[2],
                            int(values[3]),
                            int(values[4]),
                            int(values[5]),
                            values[6],
                        ),
                    )
            await self.connection.commit()
    

    '''
        SFX Event
    '''

    async def add_sfx_event(self, sfxevent: dict):
        # We need to check if values are valid from the dict
        check = await self.check_sfxevent_dict(sfxevent)
        if check.get("error"):
            return check
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO sfx_event (name, path, volume, cost, cooldown, soundcard, group_id, sfx_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sfxevent['name'], sfxevent['path'], sfxevent['volume'], sfxevent['cost'], sfxevent['cooldown'], sfxevent['soundcard'], sfxevent['group_id'], sfxevent['sfx_id'])
            )
            await self.connection.commit()

        return {"success": "SFX Event added successfully"}
    
    async def check_sfxevent_dict(self, sfxevent: dict):
        self.logger.debug(f"{sfxevent} -> {type(sfxevent)}")
        if not sfxevent['name']:
            return {"error": "Name is required"}
        if await self.is_name_exists_sfx_event(sfxevent['name']):
            return {"error": "Name already exists"}
        
        if not sfxevent['path']:
            return {"error": "Path is required"}
        if not sfxevent['volume']:
            return {"error": "Volume is required"}
        if not sfxevent['cost']:
            return {"error": "Cost is required"}
        if not sfxevent['cost'].isdigit():
            return {"error": "Cost must be a number"}
        
        cost = int(sfxevent['cost'])
        if cost < 0:
            return {"error": "Cost must be greater than 0"}
        
        if not sfxevent['cooldown']:
            return {"error": "Cooldown is required"}
        if not sfxevent['cooldown'].isdigit():
            return {"error": "Cooldown must be a number"}
        
        cooldown = int(sfxevent['cooldown'])
        if cooldown < 0:
            return {"error": "Cooldown must be greater than 0"}

        if not sfxevent['soundcard']:
            return {"error": "Soundcard is required"}
        if not sfxevent['group_id']:
            return {"error": "Group ID is required"}
        if not sfxevent['sfx_id']:
            return {"error": "SFX ID is required"}
        
        return {"success": "All values are valid"}

    async def is_name_exists_sfx_event(self, name) -> bool:
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM sfx_event WHERE name = ?", (name,))
            return await cursor.fetchone() is not None

    async def get_all_sfx_events(self):
        async with self.connection.execute("SELECT * FROM sfx_event") as cursor:
            sfx_events = await cursor.fetchall()

        sfx = [asdict(SFXEvent(*event)) for event in sfx_events]

        return sfx
    
    async def delete_sfx_event(self, msg):
        name = msg["name"]
        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx_event WHERE name = ?", (name,))
            await self.connection.commit()
        
        return {"success": "SFX Event deleted successfully"}
    

    '''
        SFX Base
    '''

    async def add_sfx(self, sfx: dict):
        # We need to check if values are valid from the dict
        check = await self.check_sfx_dict(sfx)
        if check.get("error"):
            return check
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO sfx (group_id, name, volume, cost, cooldown, soundcard) VALUES (?, ?, ?, ?, ?, ?)",
                (sfx['group_id'], sfx['name'], sfx['volume'], sfx['cost'], sfx['cooldown'], sfx['soundcard'])
            )
            await self.connection.commit()

        return {"success": "SFX added successfully"}
    
    async def check_sfx_dict(self, sfx: dict):
        self.logger.debug(f"{sfx} -> {type(sfx)}")
        if not sfx['group_id']:
            return {"error": "Group ID is required"}
        
        if not sfx['name']:
            return {"error": "Name is required"}
        if sfx['name'].isalnum():
            return {"error": "Name must be alphanumeric"}
        if await self.is_name_exists_sfx(sfx['name']):
            return {"error": "Name already exists"}
        
        if not sfx['volume']:
            return {"error": "Volume is required"}
        if not sfx['volume'].isdigit():
            return {"error": "Volume must be a number"}

        volume = int(sfx['volume'])

        if volume < 0 or volume > 100:
            return {"error": "Volume must be between 0 and 100"}

        if not sfx['cost']:
            return {"error": "Cost is required"}
        if not sfx['cost'].isdigit():
            return {"error": "Cost must be a number"}
        
        cost = int(sfx['cost'])
        if cost < 0:
            return {"error": "Cost must be greater than 0"}

        if not sfx['cooldown']:
            return {"error": "Cooldown is required"}
        if not sfx['cooldown'].isdigit():
            return {"error": "Cooldown must be a number"}
        
        cooldown = int(sfx['cooldown'])
        if cooldown < 0:
            return {"error": "Cooldown must be greater than 0"}
        
        if not sfx['soundcard']:
            return {"error": "Soundcard is required"}
        
        return {"success": "All values are valid"}
    
    async def is_name_exists_sfx(self, name) -> bool:
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM sfx WHERE name = ?", (name,))
            return await cursor.fetchone() is not None
    
    async def get_last_sfx_id(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT id FROM sfx ORDER BY id DESC LIMIT 1")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_all_sfx(self):
        async with self.connection.execute("SELECT * FROM sfx") as cursor:
            sfx = await cursor.fetchall()

        sfx = [asdict(SFX(*s)) for s in sfx]

        return sfx
    
    async def delete_sfx(self, msg):
        name = msg["name"]
        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx WHERE name = ?", (name,))
            await self.connection.commit()
        
        return {"success": "SFX deleted successfully"}

    ''' 
        SFX Group 
    '''

    async def add_sfx_group(self, sfxgroup: dict):
        # We need to check if values are valid from the dict
        check = await self.check_sfxgroup_dict(sfxgroup)
        if check.get("error"):
            return check
        
        id = await self.get_last_id() + 1
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO sfx_groups (id, name, category, description, status) VALUES (?, ?, ?, ?, ?)",
                (id, sfxgroup['name'], sfxgroup['category'], sfxgroup['description'], 1)
            )
            await self.connection.commit()

        return {"success": "SFX Group added successfully"}
    
    async def check_sfxgroup_dict(self, sfxgroup: dict):
        self.logger.debug(f"{sfxgroup} -> {type(sfxgroup)}")
        if not sfxgroup['name']:
            return {"error": "Name is required"}
        if await self.is_name_exists(sfxgroup['name']):
            return {"error": "Name already exists"}
        if not sfxgroup['category']:
            return {"error": "Category is required"}
        if not sfxgroup['description']:
            return {"error": "Description is required"}
        
        return {"success": "All values are valid"}
    
    async def is_name_exists(self, name) -> bool:
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM sfx_groups WHERE name = ?", (name,))
            return await cursor.fetchone() is not None
        
    async def get_last_sfx_group_id(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT id FROM sfx_groups ORDER BY id DESC LIMIT 1")
            result = await cursor.fetchone()
            return result[0] if result else 0
        
    async def get_all_sfx_groups(self):
        async with self.connection.execute("SELECT * FROM sfx_groups") as cursor:
            sfx_groups = await cursor.fetchall()

        sfx = [asdict(SFXGroup(*group)) for group in sfx_groups]

        return sfx
    
    async def delete_sfx_group(self, msg):
        name = msg["name"]
        # get the id of the sfx group
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT id FROM sfx_groups WHERE name = ?", (name,))
            id = await cursor.fetchone()
            # deal with the case it's None or Tuple with none or Tupe
            id = id[0] if id else 1

        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx_groups WHERE name = ?", (name,))
            await self.connection.commit()

        # delete all sfx from the sfx group
        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx WHERE group_id = ?", (id,))
            await self.connection.commit()

        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx_event WHERE group_id = ?", (id,))
            await self.connection.commit()
        
        return {"success": "SFX Group deleted successfully"}