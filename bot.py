import discord
from discord import app_commands
import json
import os
import asyncio
import re
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
PROTECTED_FILE = "protected-channels.json"

TYPE_MAP = {
    "text": discord.ChannelType.text,
    "voice": discord.ChannelType.voice,
    "forum": discord.ChannelType.forum,
    "announcement": discord.ChannelType.news,
    "news": discord.ChannelType.news,
    "stage": discord.ChannelType.stage_voice,
}


def load_protected() -> set[int]:
    if not os.path.exists(PROTECTED_FILE):
        return set()
    with open(PROTECTED_FILE, "r") as f:
        return set(json.load(f))


def save_protected(ids: set[int]):
    with open(PROTECTED_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)


def parse_plan(plan_str: str) -> list[dict]:
    raw = plan_str.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


async def create_channel(category, name: str, ch_type: discord.ChannelType):
    if ch_type == discord.ChannelType.text:
        return await category.create_text_channel(name)
    elif ch_type == discord.ChannelType.voice:
        return await category.create_voice_channel(name)
    elif ch_type == discord.ChannelType.forum:
        return await category.create_forum_channel(name)
    elif ch_type == discord.ChannelType.news:
        return await category.create_text_channel(name, news=True)
    elif ch_type == discord.ChannelType.stage_voice:
        return await category.create_stage_channel(name)
    return await category.create_text_channel(name)


async def run_setup(guild: discord.Guild, structure: list[dict]) -> str:
    protected = load_protected()
    created = 0
    errors = []

    for cat_data in structure:
        cat_name = cat_data["name"]
        channels = cat_data.get("channels", [])

        existing_cat = discord.utils.get(guild.categories, name=cat_name)

        if existing_cat:
            protected_in_cat = [c for c in existing_cat.channels if c.id in protected]
            if protected_in_cat:
                for ch in existing_cat.channels:
                    if ch.id not in protected:
                        try:
                            await ch.delete()
                        except Exception as e:
                            errors.append(f"Could not delete {ch.name}: {e}")
            else:
                try:
                    await existing_cat.delete()
                    existing_cat = None
                except Exception as e:
                    errors.append(f"Could not delete category {cat_name}: {e}")
                    continue

        if existing_cat is None:
            try:
                existing_cat = await guild.create_category(cat_name)
                created += 1
            except Exception as e:
                errors.append(f"Could not create category {cat_name}: {e}")
                continue

        for ch in channels:
            ch_name = ch["name"]
            ch_type = TYPE_MAP.get(ch.get("type", "text").lower(), discord.ChannelType.text)

            is_protected = any(c.id in protected for c in existing_cat.channels)
            existing = discord.utils.get(existing_cat.channels, name=ch_name)

            if existing and existing.id in protected:
                continue

            if existing:
                try:
                    await existing.delete()
                except Exception as e:
                    errors.append(f"Could not delete {ch_name}: {e}")
                    continue

            for attempt in range(3):
                try:
                    await create_channel(existing_cat, ch_name, ch_type)
                    created += 1
                    break
                except (discord.HTTPException, discord.ServerDisconnectedError) as e:
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        errors.append(f"Could not create {ch_name}: {e}")

    parts = [f"**Setup complete!**\n- {created} items created"]
    if errors:
        parts.append(f"- {len(errors)} error(s):\n" + "\n".join(errors[:5]))
    return "\n".join(parts)


class BotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Bot online as {self.user}", flush=True)
        for g in self.guilds:
            print(f"  Guild: \"{g.name}\" ({g.id})", flush=True)

        try:
            synced = await self.tree.sync()
            print(f"  Registered {len(synced)} command(s) globally", flush=True)
        except Exception as e:
            print(f"  Sync error: {e}", flush=True)
            try:
                synced = await self.tree.sync(guild=discord.Object(id=GUILD_ID))
                print(f"  Registered {len(synced)} command(s) to guild", flush=True)
            except Exception as e2:
                print(f"  Guild sync also failed: {e2}", flush=True)


client = BotClient()

# ── Commands ──────────────────────────────────────────────────────

async def help_fn(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Server Builder Bot",
        description="Create and manage your Discord server structure.",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="/setup-server [plan]",
        value="Create categories and channels from a JSON plan.\n"
              "Pass the plan as a JSON code block or inline.",
        inline=False,
    )
    embed.add_field(
        name="/protect [channel_id]",
        value="Protect a channel from being deleted on next setup.",
        inline=False,
    )
    embed.add_field(
        name="/unprotect [channel_id]",
        value="Remove protection from a channel.",
        inline=False,
    )
    embed.add_field(
        name="/protected",
        value="List all protected channels.",
        inline=False,
    )
    embed.add_field(
        name="Plan format",
        value=(
            "```json\n"
            '[{"name":"Category","channels":[{"name":"general","type":"text"},{"name":"Voice","type":"voice"}]}]\n'
            "```\n"
            "Types: `text`, `voice`, `forum`, `announcement`, `stage`"
        ),
        inline=False,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.describe(plan="JSON plan with categories and channels")
async def setup_fn(interaction: discord.Interaction, plan: str):
    try:
        structure = parse_plan(plan)
    except json.JSONDecodeError as e:
        await interaction.response.send_message(
            f"Invalid JSON plan: {e}", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    result = await run_setup(interaction.guild, structure)
    await interaction.followup.send(result, ephemeral=True)


@app_commands.describe(channel_id="Channel ID or #mention to protect")
async def protect_fn(interaction: discord.Interaction, channel_id: str):
    match = re.match(r"<#?(\d+)>", channel_id.strip())
    if match:
        cid = int(match.group(1))
    else:
        cid = int(channel_id.strip())

    ch = interaction.guild.get_channel(cid)
    if not ch:
        await interaction.response.send_message("Channel not found.", ephemeral=True)
        return

    protected = load_protected()
    protected.add(cid)
    save_protected(protected)
    await interaction.response.send_message(
        f"Protected {ch.mention}", ephemeral=True
    )


@app_commands.describe(channel_id="Channel ID or #mention to unprotect")
async def unprotect_fn(interaction: discord.Interaction, channel_id: str):
    match = re.match(r"<#?(\d+)>", channel_id.strip())
    if match:
        cid = int(match.group(1))
    else:
        cid = int(channel_id.strip())

    protected = load_protected()
    if cid in protected:
        protected.remove(cid)
        save_protected(protected)
        await interaction.response.send_message(
            f"Unprotected <#{cid}>", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Channel is not protected.", ephemeral=True
        )


async def list_protected_fn(interaction: discord.Interaction):
    protected = load_protected()
    if not protected:
        await interaction.response.send_message(
            "No protected channels.", ephemeral=True
        )
        return

    lines = []
    for cid in sorted(protected):
        ch = interaction.guild.get_channel(cid)
        if ch:
            lines.append(f"- {ch.mention} (`{cid}`)")
        else:
            lines.append(f"- `{cid}` (not found)")

    await interaction.response.send_message(
        "**Protected channels:**\n" + "\n".join(lines), ephemeral=True
    )


help_cmd = app_commands.Command(
    name="help",
    description="Show available commands and plan format.",
    callback=help_fn,
)

setup_cmd = app_commands.Command(
    name="setup-server",
    description="Create categories and channels from a JSON plan.",
    callback=setup_fn,
)
setup_cmd.default_permissions = discord.Permissions(administrator=True)

protect_cmd = app_commands.Command(
    name="protect",
    description="Protect a channel from deletion on next setup.",
    callback=protect_fn,
)
protect_cmd.default_permissions = discord.Permissions(administrator=True)

unprotect_cmd = app_commands.Command(
    name="unprotect",
    description="Remove protection from a channel.",
    callback=unprotect_fn,
)
unprotect_cmd.default_permissions = discord.Permissions(administrator=True)

list_protected_cmd = app_commands.Command(
    name="protected",
    description="List all protected channels.",
    callback=list_protected_fn,
)
list_protected_cmd.default_permissions = discord.Permissions(administrator=True)

bot_cmds = [help_cmd, setup_cmd, protect_cmd, unprotect_cmd, list_protected_cmd]
for cmd in bot_cmds:
    client.tree.add_command(cmd)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env")
    if not os.getenv("GUILD_ID"):
        raise ValueError("GUILD_ID is not set in .env")
    client.run(TOKEN)
