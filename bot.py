import discord
from discord import app_commands
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
TEMPLATE_FILE = "server-template.json"


def load_template(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class BotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.add_command(setup_server)
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))

    async def on_ready(self):
        print(f"Bot logged in as {self.user}")


client = BotClient()


@client.tree.command(
    name="setup-server",
    description="Create all categories and channels from the server template file",
)
@app_commands.default_permissions(administrator=True)
async def setup_server(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    structure = load_template(TEMPLATE_FILE)
    guild = interaction.guild

    created = 0
    skipped = 0

    for category_data in structure:
        cat_name = category_data["name"]
        channels = category_data.get("channels", [])

        category = discord.utils.get(guild.categories, name=cat_name)
        if category is None:
            category = await guild.create_category(cat_name)
            created += 1
        else:
            skipped += 1

        for ch in channels:
            existing = discord.utils.get(category.channels, name=ch["name"])
            if existing is None:
                if ch["type"] == "voice":
                    await category.create_voice_channel(ch["name"])
                else:
                    await category.create_text_channel(ch["name"])
                created += 1
            else:
                skipped += 1

    await interaction.followup.send(
        f"**Setup complete!**\n"
        f"- {created} items created\n"
        f"- {skipped} items already exist (skipped)",
        ephemeral=True,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env")
    if not os.getenv("GUILD_ID"):
        raise ValueError("GUILD_ID is not set in .env")
    client.run(TOKEN)
