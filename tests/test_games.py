from dataclasses import fields
import sys
import os
import unittest
import aiosqlite
import argparse

import random
import string

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from modules.games.common import GamesCog, Game

class TestGamesCog(unittest.IsolatedAsyncioTestCase):
    # randomly fill automatically a dataclass with value based on the type
    async def asyncSetUp(self):
        # path of the games.sqlite from data/database

        self.connection = await aiosqlite.connect("data/database/games.sqlite")  # Use in-memory database for testing
        self.games_cog = GamesCog(self.connection)

        await self.games_cog.create_table()

    async def test_001_add_game(self):
        game = Game(id=1, name="Test Game", category="Test Category", description="Test Description", status=0)
        await self.games_cog.add_game(game)
        cursor = await self.connection.execute("SELECT * FROM game WHERE id = ?", (game.id,))
        result = await cursor.fetchone()
        self.assertEqual(result[1], game.name)
        self.assertEqual(result[2], game.category)
        self.assertEqual(result[3], game.description)
        self.assertEqual(result[4], game.status)    

    async def test_002_update_game(self):
        game = Game(id=1, name="Updated Game", category="Updated Category", description="Updated Description", status=0)
        await self.games_cog.update_game(game)

        cursor = await self.connection.execute("SELECT * FROM game WHERE id = ?", (game.id,))
        result = await cursor.fetchone()

        self.assertEqual(result[1], game.name)
        self.assertEqual(result[2], game.category)
        self.assertEqual(result[3], game.description)
        self.assertEqual(result[4], game.status)

    async def test_003_delete_game(self):
        game_id = 1
        await self.games_cog.delete_game(game_id)
        cursor = await self.connection.execute("SELECT * FROM game WHERE id = ?", (game_id,))
        result = await cursor.fetchone()
        self.assertIsNone(result)

    async def asyncTearDown(self):
        await self.connection.close()

class TestMultipleGames(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connection = await aiosqlite.connect("data/database/games.sqlite")  # Use in-memory database for testing
        self.games_cog = GamesCog(self.connection)
        await self.games_cog.create_table()

    async def test_001_add_multiple_games(self):
        for i in range(200):
            game_id = i + 1  # Start from 1
            game_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            game_category = ''.join(random.choices(('RPG','Gatcha')))
            game_description = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            game_status = 0
            game = Game(id=game_id, name=game_name, category=game_category, description=game_description, status=game_status)
            await self.games_cog.add_game(game)

            # Verify that the game was added
            cursor = await self.connection.execute("SELECT * FROM game WHERE id = ?", (game_id,))
            result = await cursor.fetchone()
            self.assertEqual(result[1], game.name)
            self.assertEqual(result[2], game.category)
            self.assertEqual(result[3], game.description)
            self.assertEqual(result[4], game.status)

    async def asyncTearDown(self):
        await self.connection.close()

if __name__ == '__main__':
    # generate options with argparse one for generating the database and one for running the tests
    parser = argparse.ArgumentParser(description='Run tests for the games module')
    parser.add_argument('--generate', action='store_true', help='Generate the database')
    parser.add_argument('--test', action='store_true', help='Run the tests')
    args = parser.parse_args()
    
    if args.test:
        unittest.main(argv=[''], exit=False, verbosity=2, defaultTest="TestGamesCog")

    if args.generate:
        unittest.main(argv=[''], exit=False, verbosity=2, defaultTest="TestMultipleGames")
