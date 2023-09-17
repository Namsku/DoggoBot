import aiosqlite
from dataclasses import dataclass

@dataclass
class Channel:
    bot_name: str
    streamer_channel: str
    prefix: str
    coin_name: str
    income: int
    timeout: int

class ChannelCog():
    def __init__(self, config: dict, connection: aiosqlite.Connection) -> None:
        self.bot_name = config['bot_name']
        self.streamer_channel = config['streamer_channel']
        self.prefix = config['prefix']
        self.coin_name = config['coin_name']
        self.income = config['default_income']
        self.timeout = config['default_timeout']
        self.connection = connection
    
    async def create_table(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS channel (
                bot_name TEXT,
                streamer_channel TEXT,
                prefix TEXT,
                coin_name TEXT,
                income INTEGER,
                timeout INTEGER
            )
        """
        )

        await self.connection.commit()

    async def update_channel(self):
        await self.connection.execute(
            """
            UPDATE channel bot_name = ?, streamer_channel = ?, prefix = ?, coin_name = ?, income = ?, timeout = ? WHERE id = ?
        """,
            (self.bot_name, self.streamer_channel, self.prefix, self.coin_name, self.income, self.timeout),
        )

        await self.connection.commit()

    async def update_income(self, income: int):
        await self.connection.execute(
            """
            UPDATE channel SET income = ? WHERE streamer_channel = ?
        """,
            (income, self.streamer_channel),
        )

        await self.connection.commit()
    
    async def get_channel(self, name: str) -> Channel:
        async with self.connection.execute(
            """
            SELECT * FROM channel WHERE streamer_channel = ?
        """,
            (name,),
        ) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return Channel(*result)

    async def add_channel(self):
        await self.connection.execute(
            """
            INSERT INTO channel (streamer_channel, prefix, coin_name, income, timeout) VALUES (?, ?, ?, ?, ?)
        """,
            (self.streamer_channel, self.prefix, self.coin_name, self.income, self.timeout),
        )

        await self.connection.commit()