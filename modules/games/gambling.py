from modules.logger import Logger

from dataclasses import asdict, dataclass, fields
from twitchio.ext import commands

import aiosqlite
import random
import time


@dataclass
class Roll:
    status: int
    minimum_bet: int
    maximum_bet: int
    reward_critical_success: float
    reward_critical_failure: float
    time: int


@dataclass
class Slots:
    cost: int
    status: int
    rng_manipulation: int
    success_rate: int
    reward_mushroom: float
    reward_coin: float
    reward_coin: float
    reward_leaf: float
    reward_diamond: float
    jackpot: int
    time: int


class GamblingCog(commands.Cog):
    def __init__(self, connection: aiosqlite.Connection, bot):
        """
        Initialize the GamesCog class.

        Parameters
        ----------
        connection : aiosqlite.Connection
            Connection to the database.

        Returns
        -------
        None
        """

        self.logger = Logger(__name__)
        self.connection = connection
        self.bot = bot
        self.roll = None  # type: Roll
        self.slots = None  # type: Slots

    async def __ainit__(self) -> None:
        """
        Initialize the GamesCog class.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.logger.info("Initializing GambingCog...")
        if await self.is_slots_table_empty():
            self.logger.info("Slots table not configured. Filling")
            await self.fill_default_slots_table()

        if await self.is_roll_table_empty():
            await self.fill_default_roll_table()

        self.slots = await self.get_slots()
        self.roll = await self.get_roll()

    async def create_table(self):
        """
        Create the games table for rolls and slots.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        # create two table in one single execute
        await self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS slots (
                cost INTEGER NOT NULL,
                status INTEGER NOT NULL,
                rng_manipulation INTEGER NOT NULL,
                success_rate INTEGER NOT NULL,
                reward_mushroom REAL NOT NULL,
                reward_coin REAL NOT NULL,
                reward_leaf REAL NOT NULL,
                reward_diamond REAL NOT NULL,
                jackpot INTEGER NOT NULL,
                time INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roll (
                status INTEGER NOT NULL,
                minimum_bet INTEGER NOT NULL,
                maximum_bet INTEGER NOT NULL,
                reward_critical_success REAL NOT NULL,
                reward_critical_failure REAL NOT NULL,
                time INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS game (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                cost INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rpg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                boss INTEGER NOT NULL,
                time INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS gatcha (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                rarity INTEGER NOT NULL,
                time INTEGER NOT NULL
            );
        """
        )

    async def is_slots_table_empty(self) -> bool:
        """
        Checks if the table is empty.

        Returns
        -------
        bool
            True if the table is empty, False otherwise.
        """

        async with self.connection.execute("SELECT * FROM slots") as cursor:
            return not bool(await cursor.fetchone())

    async def is_roll_table_empty(self) -> bool:
        """
        Check if the roll table is configured.

        Parameters
        ----------
        None

        Returns
        -------
        bool
            True if the table is configured, False otherwise.
        """

        async with self.connection.execute("SELECT * FROM roll") as cursor:
            return not bool(await cursor.fetchone())

    async def fill_default_slots_table(self):
        """
        Fill the slots table with default values.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        await self.connection.execute(
            "INSERT INTO slots (cost, status, rng_manipulation, success_rate, reward_mushroom, reward_coin, reward_leaf, reward_diamond, jackpot, time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                10000,
                1,
                0,
                33,
                1.5,
                2.5,
                5,
                10,
                7777777,
                0,
            ),
        )
        await self.connection.commit()
        self.logger.info("Slots table filled.")

    async def fill_default_roll_table(self):
        """
        Fill the roll table with default values.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        await self.connection.execute(
            "INSERT INTO roll (status, minimum_bet, maximum_bet, reward_critical_success, reward_critical_failure, time) VALUES (?, ?, ?, ?, ?, ?)",
            (
                1,
                100,
                777777,
                7.777,
                6.66,
                0,
            ),
        )
        await self.connection.commit()
        self.logger.info("Roll table filled.")

    async def get_roll(self) -> Roll:
        """
        Get the roll object.

        Parameters
        ----------
        None

        Returns
        -------
        Roll
            The roll object.
        """

        async with self.connection.execute("SELECT * FROM roll") as cursor:
            roll_row = await cursor.fetchone()

        if roll_row is None:
            return None

        roll_attributes = [field.name for field in fields(Roll)]
        roll = Roll(**dict(zip(roll_attributes, roll_row)))

        return roll

    async def get_slot_spin(self) -> list:
        """
        Get the result of a slot machine.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        symbols = ["🍄", "🪙", "🍀", "💎", "💛"]
        reels = [random.choice(symbols) for _ in range(3)]

        if self.slots.success_rate < 0:
            return reels

        if self.slots.success_rate >= self.generate_random_number():
            while not all(symbol == reels[0] for symbol in reels):
                reels = [random.choice(symbols) for _ in range(3)]

        return reels

    def generate_random_number(self, min=0, max=100) -> int:
        """
        Generate a random number between min and max.

        Parameters
        ----------
        min : int
            The minimum number to generate.
        max : int
            The maximum number to generate.

        Returns
        -------
        int
            The generated number.
        """

        random.seed(time.time() ** 2 % 1000000)
        return random.randint(min, max)

    async def get_slots(self) -> Slots:
        """
        Get the slots object.

        Parameters
        ----------
        None

        Returns
        -------
        Slots
            The slots object.
        """

        async with self.connection.execute("SELECT * FROM slots") as cursor:
            slots_row = await cursor.fetchone()

        if slots_row is None:
            return None

        slots_attributes = [field.name for field in fields(Slots)]
        slots = Slots(**dict(zip(slots_attributes, slots_row)))

        return slots

    async def update_roll(self) -> None:
        """
        Update the roll object.

        Parameters
        ----------
        roll : Roll
            The roll object to update.

        Returns
        -------
        None
        """

        roll_dict = asdict(self.roll)
        sql_query = "UPDATE roll SET " + ", ".join(
            f"{key} = ?" for key in roll_dict.keys()
        )
        parameters = tuple(roll_dict.values())

        await self.connection.execute(sql_query, parameters)
        await self.connection.commit()

        self.logger.info("Roll updated.")

    async def update_slots(self) -> None:
        """
        Update the slots object.

        Parameters
        ----------
        slots : Slots
            The slots object to update.

        Returns
        -------
        None
        """

        slots_dict = asdict(self.slots)
        sql_query = "UPDATE slots SET " + ", ".join(
            f"{key} = ?" for key in slots_dict.keys()
        )
        parameters = tuple(slots_dict.values())

        await self.connection.execute(sql_query, parameters)
        await self.connection.commit()

        self.logger.info("Database info - Slots updated.")

    async def validate_value(
        self, value, value_type, name, min_value=None, max_value=None
    ) -> dict:
        if not isinstance(value, value_type):
            return {"error": f"The {name} must be a {value_type.__name__}."}

        if min_value is not None and value < min_value:
            return {"error": f"The {name} must be a positive number."}

        if max_value is not None and value > max_value:
            return {"error": f"The {name} can't be above {max_value}."}

        return None

    async def validate_form_content(self, form) -> dict:
        fields = [
            ("slots_cost", "The cost can't be empty.", "The cost must be a number."),
            (
                "slots_success_rate",
                "The success rate can't be empty.",
                "The success rate must be a number.",
            ),
            (
                "slots_mushroom",
                "The reward mushroom can't be empty.",
                "The reward mushroom must be a number.",
            ),
            (
                "slots_coin",
                "The reward coin can't be empty.",
                "The reward coin must be a number.",
            ),
            (
                "slots_leaf",
                "The reward leaf can't be empty.",
                "The reward leaf must be a number.",
            ),
            (
                "slots_diamond",
                "The reward diamond can't be empty.",
                "The reward diamond must be a number.",
            ),
            (
                "slots_jackpot",
                "The jackpot can't be empty.",
                "The jackpot must be a number.",
            ),
            (
                "slots_time",
                "The success rate can't be empty.",
                "The success rate must be a number.",
            ),
            (
                "roll_minimum_bet",
                "The minimum bet can't be empty.",
                "The minimum bet must be a number.",
            ),
            (
                "roll_maximum_bet",
                "The maximum bet can't be empty.",
                "The maximum bet must be a number.",
            ),
            (
                "roll_reward_critical_success",
                "The reward critical success can't be empty.",
                "The reward critical success must be a number.",
            ),
            (
                "roll_reward_critical_failure",
                "The reward critical failure can't be empty.",
                "The reward critical failure must be a number.",
            ),
            (
                "roll_time",
                "The time can't be empty.",
                "The time must be a number.",
            ),
        ]

        if form.get("game_choose") == "roll":
            fields = fields[8:]
        else:
            fields = fields[:8]

        for field, empty_error, digit_error in fields:
            value = form.get(field)
            if value is None:
                return {"error": empty_error}
            if field in [
                "slots_mushroom",
                "slots_coin",
                "slots_leaf",
                "slots_diamond",
                "roll_reward_critical_success",
                "roll_reward_critical_failure",
            ]:
                if not value.replace(".", "", 1).isdigit():
                    return {"error": digit_error}
            else:
                if not value.isdigit():
                    return {"error": digit_error}

        return None

    async def fill_cfg(self, form) -> dict:
        game_type = form.get("game_choose")
        cfg = {}

        if game_type == "roll":
            cfg = {
                "type": game_type,
                "minimum_bet": int(form.get(f"{game_type}_minimum_bet")),
                "maximum_bet": int(form.get(f"{game_type}_maximum_bet")),
                "reward_critical_success": float(
                    form.get(f"{game_type}_reward_critical_success")
                ),
                "reward_critical_failure": float(
                    form.get(f"{game_type}_reward_critical_failure")
                ),
                "time": int(form.get(f"{game_type}_time")),
            }
        elif game_type == "slots":
            cfg = {
                "type": game_type,
                "cost": int(form.get(f"{game_type}_cost")),
                "success_rate": int(form.get(f"{game_type}_success_rate")),
                "jackpot": int(form.get(f"{game_type}_jackpot")),
                "reward_mushroom": float(form.get(f"{game_type}_mushroom")),
                "reward_coin": float(form.get(f"{game_type}_coin")),
                "reward_leaf": float(form.get(f"{game_type}_leaf")),
                "reward_diamond": float(form.get(f"{game_type}_diamond")),
                "time": int(form.get(f"{game_type}_time")),
            }

        return cfg

    async def set_slots_config(self, cfg) -> dict:

        self.slots.cost = cfg["cost"]
        self.slots.success_rate = cfg["success_rate"]
        self.slots.reward_mushroom = cfg["reward_mushroom"]
        self.slots.reward_coin = cfg["reward_coin"]
        self.slots.reward_leaf = cfg["reward_leaf"]
        self.slots.reward_diamond = cfg["reward_diamond"]
        self.slots.jackpot = cfg["jackpot"]
        self.slots.time = int(cfg["time"])

        for key, value in cfg.items():
            error = await self.validate_value(
                value,
                int if key in ["cost", "success_rate", "jackpot", "time"] else float,
                key,
                0,
                99 if key == "success_rate" else None,
            )
            if error and key != "type":
                return error

        await self.update_slots()
        return {"success": "Slots updated."}

    async def set_roll_config(self, cfg) -> dict:
        self.roll.minimum_bet = cfg["minimum_bet"]
        self.roll.maximum_bet = cfg["maximum_bet"]
        self.roll.reward_critical_success = cfg["reward_critical_success"]
        self.roll.reward_critical_failure = cfg["reward_critical_failure"]
        self.roll.time = int(cfg["time"])

        for key, value in cfg.items():
            error = await self.validate_value(
                value,
                int if key in ["minimum_bet", "maximum_bet", "time"] else float,
                key,
                0,
            )
            if error and key != "type":
                return error

        if self.roll.maximum_bet < self.roll.minimum_bet:
            return {"error": "The maximum bet must be greater than the minimum bet."}

        await self.update_roll()
        return {"success": "Roll updated."}

    async def set_game(self, form) -> dict:
        """
        Set the game object.

        Parameters
        ----------
        cfg : dict
            The game object to set.

        Returns
        -------
        None
        """

        error_form_invalid = await self.validate_form_content(form)
        if error_form_invalid:
            return error_form_invalid

        cfg = await self.fill_cfg(form)

        if cfg["type"] == "slots":
            return await self.set_slots_config(cfg)
        elif cfg["type"] == "roll":
            return await self.set_roll_config(cfg)

        return {"error": "Invalid game."}

    async def get_spin_result(self) -> dict:
        """
        Get the slots spin.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            The slots spin.
        """

        spin = await self.get_slot_spin()
        reward = 0
        status = False

        if spin[0] == spin[1] == spin[2]:
            if spin[0] == "🍄":
                reward = int(self.slots.reward_mushroom * self.slots.cost)
            elif spin[0] == "🪙":
                reward = int(self.slots.reward_coin * self.slots.cost)
            elif spin[0] == "🍀":
                reward = int(self.slots.reward_leaf * self.slots.cost)
            elif spin[0] == "💎":
                reward = int(self.slots.reward_diamond * self.slots.cost)
            elif spin[0] == "💛":
                reward = self.slots.jackpot

            status = True

        return {
            "status": status,
            "spin": spin,
            "reward": reward,
        }

    @commands.command(name="slots")
    async def throw_slots(self, ctx: commands.Context) -> None:
        """
        Slots game.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        user = ctx.author.name.lower()

        if user not in self.bot.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        if await self.bot.usr.get_balance(user) < self.slots.cost:
            await ctx.send(f"{user} does not have enough coins.")
            return

        result = await self.get_spin_result()

        if result["reward"] == 0:
            result["reward"] = -self.slots.cost

        if result["status"]:
            await self.bot.usr.update_user_income(user, result["reward"])
            await ctx.send(
                f"{' '.join(result['spin'])} | {user} won {result['reward']} {self.bot.channel.channel.coin_name}!"
            )
        else:
            await self.bot.usr.update_user_income(user, -result["reward"])
            await ctx.send(
                f"{' '.join(result['spin'])} | {user} lost {result['reward']} {self.bot.channel.channel.coin_name}!"
            )

    @commands.command(name="gamble")
    async def gamble(self, ctx: commands.Context) -> None:
        """
        Gambles a certain amount of coins.

        Parameters
        ----------
        ctx : twitchio.Context
            The context object.

        Returns
        -------
        None
        """

        if len(ctx.message.content.split()) != 2:
            await ctx.send("Usage: !gamble <amount>")
            return

        user = ctx.author.name.lower()
        amount = ctx.message.content.split()[1]

        if not amount.isdigit():
            await ctx.send("Usage: !gamble <amount>")
            return

        amount = int(amount, 10)

        if amount < 1:
            await ctx.send("Usage: !gamble <amount>")
            return

        if user not in self.bot.channel_members:
            await ctx.send(f"{user} is not following the channel.")
            return

        if await self.bot.usr.get_balance(user) < amount:
            await ctx.send(f"{user} does not have enough coins.")
            return

        if self.roll.maximum_bet < amount:
            await ctx.send(
                f"{user} cannot bet more than {self.roll.maximum_bet} coins."
            )
            return

        if self.roll.minimum_bet > amount:
            await ctx.send(
                f"{user} cannot bet less than {self.roll.minimum_bet} coins."
            )
            return

        rng = self.generate_random_number()

        # Critical Failure
        if rng == 0:
            # change amount has negative be sure it's integer without decimals
            amount = self.roll.reward_critical_failure * amount
            amount = int(-amount)

            await self.bot.usr.update_user_income(user, amount)
            await ctx.send(
                f"{user} rolled an awful {rng} and lost {amount} {self.bot.channel.channel.coin_name}!"
            )
        elif rng == 100:
            amount = int(self.roll.reward_critical_success * amount)
            await self.bot.usr.update_user_income(user, amount)
            await ctx.send(
                f"{user} rolled a perfect {rng} and won {amount} {self.bot.channel.channel.coin_name}!"
            )
        elif rng < 50:
            await self.bot.usr.update_user_income(user, -amount)
            await ctx.send(
                f"{user} rolled a {rng} and lost {amount} {self.bot.channel.channel.coin_name}."
            )
        elif rng == 50:
            await ctx.send(f"{user} rolled a {rng} and nothing happened.")
        else:
            amount = int(2 * amount)
            await self.bot.usr.update_user_income(user, amount)
            await ctx.send(
                f"{user} rolled a {rng} and won {amount} {self.bot.channel.channel.coin_name}!"
            )
