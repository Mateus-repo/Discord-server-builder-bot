import discord
from discord import app_commands
import json
import os
import asyncio
import re
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

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
    guild = category.guild
    if ch_type == discord.ChannelType.text:
        return await guild.create_text_channel(name, category=category)
    elif ch_type == discord.ChannelType.voice:
        return await guild.create_voice_channel(name, category=category)
    elif ch_type == discord.ChannelType.forum:
        return await guild.create_forum(name, category=category)
    elif ch_type == discord.ChannelType.news:
        return await guild.create_text_channel(name, category=category, news=True)
    elif ch_type == discord.ChannelType.stage_voice:
        return await guild.create_stage_channel(name, category=category)
    return await guild.create_text_channel(name, category=category)


async def run_setup(guild: discord.Guild, structure: list[dict]) -> str:
    protected = load_protected()
    created = 0
    errors = []
    log = []

    def ll(msg: str):
        log.append(msg)
        print(msg, flush=True)

    # ── List current channels ──────────────────────────────────────
    await guild.fetch_channels()
    ll("Current channels in server:")
    for c in guild.channels:
        if isinstance(c, discord.CategoryChannel):
            ll(f"  CAT \"{c.name}\" ({c.id})")
            for sc in c.channels:
                protected_flag = " 🔒" if sc.id in protected else ""
                t = str(sc.type).split(".")[-1] if sc.type else "?"
                ll(f"    #{sc.name} ({t}){protected_flag}")
        else:
            protected_flag = " 🔒" if c.id in protected else ""
            t = str(c.type).split(".")[-1] if c.type else "?"
            ll(f"  # {c.name} ({t}){protected_flag}")

    # ── Phase 1: Delete everything unprotected ────────────────────
    ll("")
    ll("=== Deleting all unprotected channels ===")

    # Delete loose channels (not in any category)
    for ch in list(guild.channels):
        if ch.id in protected:
            continue
        if isinstance(ch, discord.CategoryChannel):
            continue
        try:
            t = str(ch.type).split(".")[-1] if ch.type else "?"
            await ch.delete()
            ll(f"  DELETED #{ch.name} ({t})")
        except Exception as e:
            ll(f"  ERROR deleting #{ch.name}: {e}")
            errors.append(f"Could not delete {ch.name}: {e}")

    # Delete categories (and their channels) if they have no protected channels
    for cat in list(guild.categories):
        protected_in_cat = [c for c in cat.channels if c.id in protected]
        if protected_in_cat:
            ll(f"  Keeping category \"{cat.name}\" (has protected channels)")
            for ch in list(cat.channels):
                if ch.id not in protected:
                    try:
                        await ch.delete()
                        t = str(ch.type).split(".")[-1] if ch.type else "?"
                        ll(f"  DELETED #{ch.name} ({t})")
                    except Exception as e:
                        ll(f"  ERROR deleting #{ch.name}: {e}")
                        errors.append(f"Could not delete {ch.name}: {e}")
        else:
            try:
                await cat.delete()
                ll(f"  DELETED category \"{cat.name}\"")
            except Exception as e:
                ll(f"  ERROR deleting category \"{cat.name}\": {e}")
                errors.append(f"Could not delete category {cat.name}: {e}")

    await guild.fetch_channels()
    await asyncio.sleep(1)

    # ── Phase 2: Create everything from plan ───────────────────────
    ll("")
    ll("=== Creating from plan ===")
    for cat_data in structure:
        cat_name = cat_data["name"]
        channels = cat_data.get("channels", [])

        existing_cat = discord.utils.get(guild.categories, name=cat_name)

        if existing_cat is None:
            try:
                existing_cat = await guild.create_category(cat_name)
                ll(f"  CREATED category \"{cat_name}\"")
                created += 1
            except Exception as e:
                ll(f"  ERROR creating category \"{cat_name}\": {e}")
                errors.append(f"Could not create category {cat_name}: {e}")
                continue

        for ch in channels:
            ch_name = ch["name"]
            ch_type_label = ch.get("type", "text").lower()
            ch_type = TYPE_MAP.get(ch_type_label, discord.ChannelType.text)

            existing = discord.utils.get(existing_cat.channels, name=ch_name)
            if existing and existing.id in protected:
                ll(f"  SKIPPED #{ch_name} (protected)")
                continue

            if existing:
                try:
                    await existing.delete()
                    ll(f"  DELETED #{ch_name} (will recreate)")
                except Exception as e:
                    ll(f"  ERROR deleting #{ch_name}: {e}")
                    errors.append(f"Could not delete {ch_name}: {e}")
                    continue

            for attempt in range(3):
                try:
                    await create_channel(existing_cat, ch_name, ch_type)
                    ll(f"  CREATED #{ch_name} ({ch_type_label})")
                    created += 1
                    break
                except Exception as e:
                    if attempt < 2:
                        ll(f"  RETRY #{ch_name} (attempt {attempt + 2})")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        ll(f"  ERROR creating #{ch_name}: {e}")
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
        name="/setup-server [plan] [file]",
        value="Create categories and channels from a JSON plan.\n"
              "Pass the plan as text or upload a `.json` file.",
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


@app_commands.describe(
    plan="JSON plan with categories and channels (or leave empty if using file)",
    file="Upload a .json file with the server plan instead of typing it",
)
async def setup_fn(
    interaction: discord.Interaction,
    plan: str = None,
    file: discord.Attachment = None,
):
    if file:
        raw = (await file.read()).decode("utf-8")
    elif plan:
        raw = plan
    else:
        await interaction.response.send_message(
            "Provide a JSON plan as text or upload a `.json` file.",
            ephemeral=True,
        )
        return

    try:
        structure = parse_plan(raw)
    except json.JSONDecodeError as e:
        await interaction.response.send_message(
            f"Invalid JSON plan: {e}", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    result = await run_setup(interaction.guild, structure)
    try:
        await interaction.followup.send(result, ephemeral=True)
    except discord.NotFound:
        # Interaction channel was deleted during setup; fallback to a visible channel
        target = interaction.guild.system_channel or discord.utils.get(
            interaction.guild.text_channels
        )
        if target:
            await target.send(result)


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


def _channel_type_str(channel) -> str:
    if isinstance(channel, discord.TextChannel):
        return "announcement" if channel.is_news() else "text"
    elif isinstance(channel, discord.VoiceChannel):
        return "voice"
    elif isinstance(channel, discord.ForumChannel):
        return "forum"
    elif isinstance(channel, discord.StageChannel):
        return "stage"
    return "text"


def _build_json_structure(guild: discord.Guild) -> list[dict]:
    structure = []
    for category in guild.categories:
        cat_entry: dict[str, object] = {"name": category.name, "channels": []}
        for channel in category.channels:
            cat_entry["channels"].append({
                "name": channel.name,
                "type": _channel_type_str(channel),
            })
        structure.append(cat_entry)

    loose = [
        c
        for c in guild.channels
        if not isinstance(c, discord.CategoryChannel) and c.category is None
    ]
    if loose:
        loose_entry: dict[str, object] = {"name": "📂 Sem Categoria", "channels": []}
        for channel in loose:
            loose_entry["channels"].append({
                "name": channel.name,
                "type": _channel_type_str(channel),
            })
        structure.append(loose_entry)

    return structure


def _build_md_structure(guild: discord.Guild) -> str:
    lines = [
        f"# 🏠 Estrutura do Servidor: {guild.name}",
        "",
        f"*Exportado em: {datetime.now():%d/%m/%Y %H:%M}*",
        "",
    ]

    for i, category in enumerate(guild.categories):
        if i > 0:
            lines.append("---")
            lines.append("")

        lines.append(f"## {category.name}")
        lines.append("")

        for channel in category.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.is_news():
                    lines.append(f"- `#{channel.name}` 📢 *announcement*")
                else:
                    lines.append(f"- `#{channel.name}`")
            elif isinstance(channel, discord.VoiceChannel):
                lines.append(f"- 🔊 {channel.name}")
            elif isinstance(channel, discord.ForumChannel):
                lines.append(f"- `#{channel.name}` 💬 *forum*")
            elif isinstance(channel, discord.StageChannel):
                lines.append(f"- 🎤 {channel.name}")
            else:
                lines.append(f"- `#{channel.name}` ({channel.type})")

        lines.append("")

    loose = [
        c
        for c in guild.channels
        if not isinstance(c, discord.CategoryChannel) and c.category is None
    ]
    if loose:
        if guild.categories:
            lines.append("---")
            lines.append("")
        lines.append("## 📂 Sem Categoria")
        lines.append("")
        for channel in loose:
            if isinstance(channel, discord.TextChannel):
                lines.append(f"- `#{channel.name}`")
            elif isinstance(channel, discord.VoiceChannel):
                lines.append(f"- 🔊 {channel.name}")
            elif isinstance(channel, discord.ForumChannel):
                lines.append(f"- `#{channel.name}` (forum)")
            elif isinstance(channel, discord.StageChannel):
                lines.append(f"- 🎤 {channel.name}")
            else:
                lines.append(f"- `#{channel.name}` ({channel.type})")
        lines.append("")

    return "\n".join(lines)


async def export_structure_fn(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    await guild.fetch_channels()

    safe_name = re.sub(r'[<>:"/\\|?*]', "_", guild.name)
    folder_path = os.path.join("servers", safe_name)
    os.makedirs(folder_path, exist_ok=True)

    md_path = os.path.join(folder_path, "estrutura.md")
    md_content = _build_md_structure(guild)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    json_path = os.path.join(folder_path, "server-template.json")
    json_content = _build_json_structure(guild)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f, indent=2, ensure_ascii=False)

    await interaction.followup.send(
        f"✅ Exportado:\n- `{md_path}`\n- `{json_path}`",
        file=discord.File(md_path),
        ephemeral=True,
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

export_cmd = app_commands.Command(
    name="export-structure",
    description="Export current server structure to a markdown file.",
    callback=export_structure_fn,
)

bot_cmds = [
    help_cmd,
    setup_cmd,
    protect_cmd,
    unprotect_cmd,
    list_protected_cmd,
    export_cmd,
]
for cmd in bot_cmds:
    client.tree.add_command(cmd)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env")
    if not os.getenv("GUILD_ID"):
        raise ValueError("GUILD_ID is not set in .env")
    client.run(TOKEN)
