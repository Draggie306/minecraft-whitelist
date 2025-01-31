import discord
from asyncio import sleep
from os import getenv
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from typing import Optional

load_dotenv(dotenv_path=".env")

print("Creating bot instance...")

# Set up intents purely for slash commands and message content.
# Message content intent is required to read console output
intents = discord.Intents.default()
intents.messages = True

client = commands.Bot(
    command_prefix="!",  # this is unused
    intents=intents,
    application_id=getenv("APPLICATION_ID"),
)

# Console channel from discordsrv to send the whitelist message
INT_CONSOLE_CHANNEL_ID = int(getenv("DISCORDSRV_CONSOLE_CHANNEL_ID"))


@client.tree.command(
    name="whitelist",
    description="MC Server -- whitelist add/remove <username>"
)
@app_commands.guild_only()
@app_commands.describe(
    operation="Which action to perform",
    username="The Minecraft username to add/remove from the whitelist (case-insensitive)",
)
@app_commands.choices(
    operation=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
    ]
)
async def whitelist(
    interaction: discord.Interaction,
    operation: app_commands.Choice[str],
    username: Optional[str] = None,
) -> None:
    """_summary_: Add or remove a user from the whitelist, or list all whitelisted users.

    Args:
        interaction (discord.Interaction): The interaction object.
        operation (app_commands.Choice[str]): String type of operation to perform which will be matched to one of "add", "remove", or "list".
        username (Optional[str], optional): The username of the player to add or remove from the whitelist. Defaults to None as it is not required for the "list" operation.

    Returns:
        _type_: None (message returned to discord)
    """
    if operation.value == "add":
        if not username:
            return await interaction.response.send_message(
                content="You need to specify the name of the user to add first!"
            )

        # Defer to prevent timeout
        await interaction.response.defer()

        channel = client.get_channel(INT_CONSOLE_CHANNEL_ID)

        # Send console commands to add the user to the whitelist and to announce it to the server
        await channel.send(f"whitelist add {username}")
        await channel.send(
            content=rf'tellraw @a {{"text":"Server: Added {username} to the whitelist","italic":true,"color":"gray"}}'
        )

        # Wait for the server to process the command
        await sleep(2)

        # Read the latest message from the console channel
        # This is a bit hacky, so TODO: use fetch_channel vs get channel to call via API not cache
        channel = client.get_channel(INT_CONSOLE_CHANNEL_ID)

        async for message in channel.history(limit=3):
            print(f"Message: {message.content}")
            if message.author == client.user:
                continue

            for line in message.content.split("\n"):
                if (
                    "whitelist" in line.lower()
                    or "that player does not exist" in line.lower()
                ):
                    # Respond to the user with the output of the command
                    return await interaction.followup.send(line)

        # and return to discord that the command was successful
        return await interaction.followup.send(
            f"Added {username} to the whitelist (could not read console response)."
        )
    if operation.value == "remove":
        return await interaction.response.send_message(
            "Nope, you can't remove people from the whitelist"
        )
        # await interaction.response.send_message(f"Whitelist remove {username}")
    if operation.value == "list":
        await interaction.response.defer()
        channel = client.get_channel(INT_CONSOLE_CHANNEL_ID)
        await channel.send("whitelist list")

        # Hacky - qait for the server to process the command
        await sleep(2)

        # Read the latest message from the console channel. TODO: change.
        channel = client.get_channel(INT_CONSOLE_CHANNEL_ID)
        async for message in channel.history(limit=3):
            print(f"Message: {message.content}")
            if message.author == client.user:
                continue

            for line in message.content.split("\n"):
                if (
                    "whitelist" in line.lower()
                    or "that player does not exist" in line.lower()
                ):
                    # Respond to the user with the output of the command
                    return await interaction.followup.send(line)

        # ... and return to discord that the command was successful
        return await interaction.followup.send(
            content=f"Added {username} to the whitelist (could not read console response)."
        )
    if operation.value == "remove":
        return await interaction.response.send_message(
            content="Nope, you can't remove people from the whitelist"
        )
        # await interaction.response.send_message(f"Whitelist remove {username}")
    if operation.value == "list":
        await interaction.response.defer()
        channel = client.get_channel(INT_CONSOLE_CHANNEL_ID)
        await channel.send("whitelist list")
        await sleep(2)
        channel = client.get_channel(INT_CONSOLE_CHANNEL_ID)
        async for message in channel.history(limit=3):
            if message.author == client.user:
                continue

            for line in message.content.split("\n"):
                if "whitelist" in line.lower():
                    return await interaction.followup.send(line)
        return await interaction.followup.send("Could not read console response.")

    # If the operation is not recognised (which should never happen) have end case just in... case
    return await interaction.response.send_message("Unknown operation")


@client.tree.command(name="map", description="View the server map")
@app_commands.guild_only()
async def view_map(interaction: discord.Interaction) -> None:
    """_summary_: Send a message with a HTTPS link to the online server map (can use Dynmap/Pl3xmap) to do this.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.send_message(
        content="The server map is available at [nottmap.geog.uk](https://nottmap.geog.uk).",
        ephemeral=False,
    )


@client.tree.command(name="ip", description="Get the server IP")
@app_commands.guild_only()
async def get_ip(interaction: discord.Interaction) -> None:
    """_summary_: Send a Discord message with the server IP to the user.

    Args:
        interaction (discord.Interaction): The interaction object.
    """
    await interaction.response.send_message(
        content="The server IP is `nott.geog.uk`.\nIf this doesn't work, the secondary IP is `oci.ibaguette.com`.",
        ephemeral=False,
    )


@client.tree.command(name="mods", description="View recommended mods")
@app_commands.guild_only()
async def view_mods(interaction: discord.Interaction) -> None:
    """_summary_: Send a message with a link to the recommended mods zipfile for the user to install.

    Args:
        interaction (discord.Interaction): The interaction object from the user.
    """
    await interaction.response.send_message(
        content="A zipfile of the recommended mods for performance is available at [this link](https://cdn.ibaguette.com/1.21.4-mods.zip).",
        ephemeral=True,
    )


@client.event
async def on_ready():
    """_summary_ : When the bot is ready, print a message and sync the slash commands.
    """
    print(f"Logged in as {client.user}")
    await client.tree.sync()
    print("Slash commands synced")


# And bam, run it
client.run(getenv("DISCORD_TOKEN"))
