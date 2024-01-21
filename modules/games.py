class gamesCog:
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection

    async def __ainit__(self) -> None:
        if not await self.is_slots_table_configured():
            await self.fill_default_slots_table()

        if not await self.is_roll_table_configured():
            await self.fill_default_roll_table()

    async def create_table(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY,
                success_rate FLOAT NOT NULL,
                cost INTEGER NOT NULL,
                reward_low FLOAT NOT NULL,
                reward_moderate FLOAT NOT NULL,
                reward_high FLOAT NOT NULL,
                jackpot INTEGER NOT NULL,
            )

            CREATE TABLE IF NOT EXISTS roll (
                id INTEGER PRIMARY KEY,
                success_rate FLOAT NOT NULL,
                cost INTEGER NOT NULL,
                reward INTEGER NOT NULL,
                critical_success FLOAT NOT NULL,
                critical_failure FLOAT NOT NULL,
            )
        """
        )

    async def is_slots_table_configured(self):
        async with self.connection.execute(
            """
            SELECT name FROM sqlite_master WHERE type='table' AND name='slots'
        """
        ) as cursor:
            return await cursor.fetchone() is not None

    async def is_roll_table_configured(self):
        async with self.connection.execute(
            """
            SELECT name FROM sqlite_master WHERE type='table' AND name='roll'
        """
        ) as cursor:
            return await cursor.fetchone() is not None

    async def fill_default_slots_table(self):
        await self.connection.execute(
            """
            INSERT INTO slots VALUES (
                1,
                0.5,
                100,
                0.5,
                0.3,
                0.2,
                10000
            )
        """
        )

    async def fill_default_roll_table(self):
        await self.connection.execute(
            """
            INSERT INTO roll VALUES (
                1,
                0.5,
                100,
                100,
                0.1,
                0.1
            )
        """
        )
