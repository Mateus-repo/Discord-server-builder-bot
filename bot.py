import discord
from discord import app_commands
import re
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
MD_FILE = "estrutura-servidor-discord.md"


def parse_markdown(filepath: str) -> dict:
    structure = {}
    current_category = None

    category_re = re.compile(r"^##\s+(.+)$")
    text_re = re.compile(r"^\s*-\s*`#(.+?)`\s*$")
    voice_re = re.compile(r"^\s*-\s*🔊\s+`(.+?)`\s*")
    voice_fallback_re = re.compile(r"^\s*-\s*🔊\s+(.+?)\s*$")

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("---") or line.startswith(">"):
                continue
            if line.startswith("# ") or line.startswith("## 💡"):
                continue

            m = category_re.match(line)
            if m:
                current_category = m.group(1).strip()
                structure[current_category] = []
                continue

            if current_category is None:
                continue

            m = text_re.match(line)
            if m:
                structure[current_category].append(
                    {"name": m.group(1).strip(), "type": "text"}
                )
                continue

            m = voice_re.match(line) or voice_fallback_re.match(line)
            if m:
                structure[current_category].append(
                    {"name": m.group(1).strip(), "type": "voice"}
                )

    return structure


class BotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.add_command(criar_servidor)
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))

    async def on_ready(self):
        print(f"✅ Bot logged in as {self.user}")


client = BotClient()


@client.tree.command(
    name="criarservidor",
    description="Cria categorias e canais a partir do ficheiro .md",
)
@app_commands.default_permissions(administrator=True)
async def criar_servidor(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    structure = parse_markdown(MD_FILE)
    guild = interaction.guild

    created = 0
    existing = 0

    for cat_name, channels in structure.items():
        category = discord.utils.get(guild.categories, name=cat_name)
        if category is None:
            category = await guild.create_category(cat_name)
            created += 1
        else:
            existing += 1

        for ch in channels:
            existing_ch = discord.utils.get(category.channels, name=ch["name"])
            if existing_ch is None:
                if ch["type"] == "voice":
                    await category.create_voice_channel(ch["name"])
                else:
                    await category.create_text_channel(ch["name"])
                created += 1
            else:
                existing += 1

    await interaction.followup.send(
        f"**Processo concluído!**\n"
        f"- {created} itens criados\n"
        f"- {existing} itens já existentes (ignorados)",
        ephemeral=True,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN não definido no .env")
    if not os.getenv("GUILD_ID"):
        raise ValueError("GUILD_ID não definido no .env")
    client.run(TOKEN)
