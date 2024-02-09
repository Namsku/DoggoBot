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


class SFXCog:
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection
        self.sfx = {}
        self.load_sfx()

        # init the sounds extension
        self.player = sounds.AudioPlayer(callback=self.reset_player)
    
    async def load_sfx(self):
        query = "SELECT * FROM sfx"
        sfx = self.connection.execute(query)
        for s in sfx:
            self.sfx[s[0]] = SFX(*s)
    
    async def reset_player(self):
        self.player.volume = 100
        self.player.stop()
    
    