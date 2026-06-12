import discord
from discord import app_commands
from discord.http import Route
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
TEMPLATE_FILE = "server-template.json"


def load_template(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


async def setup_server(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    structure = load_template(TEMPLATE_FILE)
    guild = interaction.guild

    for category in guild.categories:
        await category.delete()

    created = 0

    for category_data in structure:
        cat_name = category_data["name"]
        channels = category_data.get("channels", [])

        category = await guild.create_category(cat_name)
        created += 1

        for ch in channels:
            if ch["type"] == "voice":
                await category.create_voice_channel(ch["name"])
            else:
                await category.create_text_channel(ch["name"])
            created += 1

    await interaction.followup.send(
        f"**Setup complete!**\n"
        f"- All existing categories deleted\n"
        f"- {created} items created from template",
        ephemeral=True,
    )


class BotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Bot online as {self.user}", flush=True)
        print(f"In {len(self.guilds)} guild(s)", flush=True)
        for g in self.guilds:
            print(f"  Guild: \"{g.name}\" ({g.id})", flush=True)
            if g.id == GUILD_ID:
                print("  -> GUILD_ID matches", flush=True)

        cmd_data = setup_cmd.to_dict()
        success = False

        try:
            synced = await self.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"  guild sync: {len(synced)} command(s)", flush=True)
            success = len(synced) > 0
        except Exception as e:
            print(f"  guild sync error: {e}", flush=True)

        if not success:
            try:
                synced = await self.tree.sync()
                print(f"  global sync: {len(synced)} command(s)", flush=True)
                success = len(synced) > 0
            except Exception as e:
                print(f"  global sync error: {e}", flush=True)

        if not success:
            try:
                await self.http.request(
                    Route("PUT",
                          "/applications/{app_id}/guilds/{guild_id}/commands",
                          app_id=self.user.id, guild_id=GUILD_ID),
                    json=[cmd_data],
                )
                print("  direct API (guild): done", flush=True)
                success = True
            except Exception as e:
                print(f"  direct API (guild) error: {e}", flush=True)

        if not success:
            try:
                await self.http.request(
                    Route("PUT",
                          "/applications/{app_id}/commands",
                          app_id=self.user.id),
                    json=[cmd_data],
                )
                print("  direct API (global): done", flush=True)
                success = True
            except Exception as e:
                print(f"  direct API (global) error: {e}", flush=True)

        if success:
            print("Slash command registered!", flush=True)
        else:
            print("All registration methods failed!", flush=True)


client = BotClient()

setup_cmd = app_commands.Command(
    name="setup-server",
    description="Delete all categories and recreate from the server template file",
    callback=setup_server,
)
setup_cmd.default_permissions = discord.Permissions(administrator=True)
client.tree.add_command(setup_cmd)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env")
    if not os.getenv("GUILD_ID"):
        raise ValueError("GUILD_ID is not set in .env")
    client.run(TOKEN)
