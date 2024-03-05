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

@dataclass!n
class SFX:
    id: int
    group_id: int
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
            dataclasses = [SFXGroup, SFX, SFXEvent]
            for dataclass in dataclasses:
                table_name = dataclass.__name__.lower()
                columns = ", ".join(self.get_column_definition(field) for field in fields(dataclass))
                query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {columns}
                    )
                """
                await self.connection.execute(query)
                await self.connection.commit()

    def get_column_definition(self, field: Field):
        column_type = self.get_sqlite_type(field.type)
        constraints = "NOT NULL" if field.default_factory == dataclasses.MISSING else ""
        if field.name == "id":
            constraints += " PRIMARY KEY AUTOINCREMENT"
        return f"{field.name} {column_type} {constraints}"

    def get_sqlite_type(self, type_):
        if type_ == int:
            return "INTEGER"
        elif type_ == str:
            return "TEXT"
        elif type_ == bool:
            return "INTEGER"
        else:
            return "BLOB"
    
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
        dest_folder.mkdir(parents=True, exist_ok=True)

        for source_path in source_folder.glob("*.[mM][pP]3") + source_folder.glob("*.[wW][aA][vV]"):
            hash_name = await self.hash_file(source_path)
            dest_path = dest_folder / (hash_name + source_path.suffix)

            if not dest_path.exists():
                dest_path.write_bytes(source_path.read_bytes())
                await self.connection.execute(
                    "INSERT INTO sfx (name, path, volume, cost, cooldown) VALUES (?, ?, ?, ?, ?)",
                    (source_path.name, str(dest_path), 100, 1000, 10),
                )
                await self.connection.commit()

    async def export_sfx_full_config(self, dest_folder=Path("data/sfx")):
        await self.copy_sfx_files(Path("data/sfx"), dest_folder)

        zip_file_path = dest_folder / "sfx_export.zip"
        with closing(zipfile.ZipFile(zip_file_path, "w")) as zip_file:
            for sound_file in dest_folder.glob("*"):
                zip_file.write(sound_file, arcname=sound_file.name)

            sfx = await self.connection.execute("SELECT * FROM sfx")
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
        
        await self.connection.execute(
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
        async with self.connection.execute("SELECT * FROM sfx_event WHERE name = ?", (name,)) as cursor:
            return await cursor.fetchone() is not None

    async def get_all_sfx_events(self):
        async with self.connection.execute("SELECT * FROM sfx_event") as cursor:
            sfx_events = await cursor.fetchall()

        sfx = [asdict(SFXEvent(*event)) for event in sfx_events]

        return sfx
    
    async def delete_sfx_event(self, msg):
        name = msg["name"]
        await self.connection.execute("DELETE FROM sfx_event WHERE name = ?", (name,))
        await self.connection.commit()
        
        return {"success": "SFX Event deleted successfully"}

    '''
        SFX Base
    '''

    async def add_sfx(self, group_id: int):
        # We need to check if values are valid from the dict  
        if self.player.active_device is None:
            self.logger.error("No default soundcard detected, selecting a random one")
            # get a random value from dictionary self.player.devices
            value = list(self.player.devices.values())[0].name
        else:
            value = self.player.active_device
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO sfx (id, group_id, volume, cost, cooldown, soundcard) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    await self.get_last_sfx_id() + 1,
                    group_id, 
                    50, 
                    0, 
                    0, 
                    value
                )
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
        check = await self.check_sfxgroup_dict(sfxgroup)
        if check.get("error"):
            return check
        
        id = await self.get_last_sfx_group_id() + 1
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO sfx_groups (id, name, category, description, status) VALUES (?, ?, ?, ?, ?)",
                (id, sfxgroup['name'], sfxgroup['category'], sfxgroup['description'], 1)
            )
            await self.connection.commit()

        result = await self.add_sfx(id)
        if result.get("error"):
            return result

        return {"success": "SFX Group added successfully"}
    
    async def check_sfxgroup_dict(self, sfxgroup: dict):
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
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT id FROM sfx_groups WHERE name = ?", (name,))
            id = await cursor.fetchone()
            id = id[0] if id else 1

        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx_groups WHERE name = ?", (name,))
            await self.connection.commit()

        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx WHERE group_id = ?", (id,))
            await self.connection.commit()

        async with self.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM sfx_event WHERE group_id = ?", (id,))
            await self.connection.commit()
        
        return {"success": "SFX Group deleted successfully"}
    
    async def get_sfx_from_group_name(self, name) -> SFX:
        id = 0
        
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT id FROM sfx_groups WHERE name = ?", (name,))
            id = await cursor.fetchone()
            id = id[0] if id else 1

        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM sfx WHERE group_id = ?", (id,))
            sfx = await cursor.fetchone()

        return SFX(*sfx)

    async def get_all_sfx_events_from_group_name(self, name) -> list[SFXEvent]:
        id = 0
        
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT id FROM sfx_groups WHERE name = ?", (name,))
            id = await cursor.fetchone()
            id = id[0] if id else 1
        
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM sfx_event WHERE group_id = ?", (id,))
            sfx = await cursor.fetchall()
        
        sfx = [SFXEvent(*event) for event in sfx]

        return sfx
