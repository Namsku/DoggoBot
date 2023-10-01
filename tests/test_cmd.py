import asyncio
import aiosqlite


async def get_commands():
    # Connect to the database
    async with aiosqlite.connect("../data/database/cmd.sqlite") as db:
        # Get all the commands from the database
        async with db.execute("SELECT * FROM cmd") as cursor:
            commands = await cursor.fetchall()

    # Convert the commands to a list
    cmd_list = [command for command in commands]

    # Return the list of commands
    return cmd_list


# Run the coroutine and print the list of commands
content = asyncio.run(get_commands())
print(content)
