import aiosqlite
import asyncio

# generate 1000 random users for testings
import random
import string

from dataclasses import dataclass


@dataclass
class User:
    # User settings
    id: int
    username: str
    income: int

    message_count: int

    bot: bool
    follower: bool
    subscriber: bool
    mod: bool

    # Game/SFX settings
    gamble_lock: str
    roll_lock: str
    rpg_lock: str
    sfx_lock: str
    slots_lock: str

    # Moderation settings
    ban_time: str
    warning: int


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


async def add_user(connection: aiosqlite.Connection, user: User) -> None:
    """
    Adds a user to the database.

    Parameters
    ----------
    connection : aiosqlite.Connection
        The connection to the database.
    user : User
        The user object.

    Returns
    -------
    None
    """

    await connection.execute(
        """
                INSERT INTO users (
                    username,
                    income,
                    message_count,
                    bot,
                    follower,
                    subscriber,
                    mod,
                    gamble_lock,
                    roll_lock,
                    rpg_lock,
                    sfx_lock,
                    slots_lock,
                    ban_time,
                    warning
                    )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
            """,
        (
            user.username,
            user.income,
            user.message_count,
            user.bot,
            user.follower,
            user.subscriber,
            user.mod,
            user.gamble_lock,
            user.roll_lock,
            user.rpg_lock,
            user.sfx_lock,
            user.slots_lock,
            user.ban_time,
            user.warning,
        ),
    )

    await connection.commit()


async def generate_users():
    connection_user = await aiosqlite.connect("data/database/user.sqlite")

    await connection_user.execute(
        """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                income INTEGER,
                message_count INTEGER,
                bot INTEGER,
                follower INTEGER,
                subscriber INTEGER,
                mod INTEGER,
                gamble_lock TEXT,
                roll_lock TEXT,
                rpg_lock TEXT,
                sfx_lock TEXT,
                slots_lock TEXT,
                ban_time TEXT,
                warning INTEGER
            )
        """
    )

    await connection_user.commit()

    for i in range(30):
        username = get_random_string(15)
        income = random.randint(1, 10000)

        message_count = random.randint(1, 100)

        bot = random.choice([True, False])
        follower = random.choice([True, False])
        subscriber = random.choice([True, False])
        mod = random.choice([True, False])

        # Game/SFX settings
        gamble_lock = random.choice([True, False])
        roll_lock = random.choice([True, False])
        rpg_lock = random.choice([True, False])
        sfx_lock = random.choice([True, False])
        slots_lock = random.choice([True, False])

        # Moderation settings
        ban_time = random.randint(1, 10000000)
        warning = random.randint(1, 10000000)

        user = User(
            i,
            username,
            income,
            message_count,
            bot,
            follower,
            subscriber,
            mod,
            gamble_lock,
            roll_lock,
            rpg_lock,
            sfx_lock,
            slots_lock,
            ban_time,
            warning,
        )

        await add_user(connection_user, user)

        print(f"User {i} created -> {user}")


asyncio.run(generate_users())
