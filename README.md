# Discord Server Builder Bot

A Discord bot that automatically creates categories and channels from a JSON template file.

## How to use

### 1. Create the bot on Discord Developer Portal

1. Go to https://discord.com/developers/applications
2. Click **New Application** and give it a name
3. Go to **Bot** tab → **Add Bot** → copy the **Token**
4. Go to **OAuth2 > URL Generator**:
   - Scopes: `bot`
   - Permissions: `Manage Channels`
5. Open the generated URL to invite the bot to your server

### 2. Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create config file
cp .env.example .env
```

Fill in the `.env` file:

```
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
```

> To get the `GUILD_ID`: enable **Developer Mode** in Discord (Settings > Advanced), right-click your server name → **Copy Server ID**.

### 3. Create your server template

```bash
# Copy the example template to get started
cp server-template.example.json server-template.json
```

Then edit `server-template.json` with your desired structure. See the format below.

### 4. Run

```bash
python bot.py
```

In Discord, use the command:

```
/setup-server
```

The bot will create all categories and channels defined in `server-template.json` that don't already exist in the server.

## Project structure

```
├── bot.py                          # Main bot script
├── server-template.json            # Server structure template (edit this)
├── requirements.txt                # Python dependencies
├── .env.example                    # Config template
├── .gitignore
├── estrutura-servidor-discord.md   # Original server structure (reference only)
├── plano-bot-criacao-canais.md     # Original project plan (Portuguese)
└── README.md
```

## Template format (`server-template.json`)

The bot reads a JSON file with the following structure:

```json
[
  {
    "name": "Category Name",
    "channels": [
      { "name": "channel-name", "type": "text" },
      { "name": "Voice Channel", "type": "voice" }
    ]
  }
]
```

- `name` (category): the category name displayed in Discord (emojis supported)
- `channels`: list of channels in that category
  - `name`: the channel name
  - `type`: `"text"` for text channels, `"voice"` for voice channels

## Security

The `/setup-server` command is restricted to server administrators.
Never share the `.env` file (it contains your bot token).
