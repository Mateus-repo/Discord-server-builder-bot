# Discord Server Builder Bot

A Discord bot that rebuilds your server from a JSON plan — deletes all unprotected channels/categories and recreates them according to your template.

## Features

- **Full server reset** — deletes every unprotected channel and category, then recreates from your plan
- **Channel protection** — mark specific channels as protected so they survive resets
- **5 channel types** — text, voice, forum, announcement, stage
- **Slash commands** — `/setup-server`, `/help`, `/protect`, `/unprotect`, `/protected`
- **File upload support** — paste the JSON inline *or* upload a `.json` file
- **Admin-only** — all destructive commands are restricted to administrators

## How to use

### 1. Create a Discord application

1. Go to https://discord.com/developers/applications
2. Click **New Application** and name it
3. **Bot** tab → **Add Bot** → copy the **Token**
4. **OAuth2 > URL Generator**:
   - Scopes: `bot` + `applications.commands`
   - Permissions: `Manage Channels` (or `Administrator`)
5. Open the generated URL to invite the bot to your server

### 2. Setup

```bash
# Clone the repo
git clone https://github.com/Strefiz/Discord-server-builder-bot.git
cd Discord-server-builder-bot

# Install dependencies
pip install -r requirements.txt

# Create config file
cp .env.example .env
```

Fill in `.env`:

```
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here
```

> To get `GUILD_ID`: enable **Developer Mode** in Discord (Settings > Advanced), right-click your server → **Copy Server ID**.

### 3. Create your plan

```bash
# Copy the example template and edit it
cp server-template.example.json server-template.json
```

Edit `server-template.json` with your desired structure (see format below).

### 4. Run

```bash
python bot.py
```

In Discord, use:

```
/setup-server file: (attach server-template.json)
```

> **Tip**: if your plan is small you can paste it inline instead: `/setup-server plan: [your JSON here]`

## Commands

| Command | Description |
|---|---|
| `/setup-server [plan] [file]` | Reset the server: delete unprotected channels/categories and recreate from plan |
| `/help` | Show available commands and plan format reference |
| `/protect <channel_id>` | Protect a channel from being deleted on the next setup |
| `/unprotect <channel_id>` | Remove protection from a channel |
| `/protected` | List all protected channels |

## Template format

```json
[
  {
    "name": "📋 Category Name",
    "channels": [
      { "name": "general", "type": "text" },
      { "name": "Voice", "type": "voice" },
      { "name": "Showcase", "type": "forum" },
      { "name": "News", "type": "announcement" },
      { "name": "Stage", "type": "stage" }
    ]
  }
]
```

### Channel types

| Type | Discord type | Description |
|---|---|---|
| `"text"` | Text channel | Regular chat channel |
| `"voice"` | Voice channel | Voice chat |
| `"forum"` | Forum | Thread-based discussion |
| `"announcement"` | Announcement channel | Publishing channel |
| `"stage"` | Stage channel | Live audio events |

### File vs inline

- **File** (recommended): upload your `server-template.json` with `/setup-server file:`
- **Inline**: pass the full JSON as a string with `/setup-server plan:` (limited to Discord's character limit)

## Channel protection

Channels you want to keep (e.g. a forum with important posts) can be protected:

```
/protect 123456789012345678
```

The bot will:
- Skip deleting that channel during setup
- Keep its parent category (even if the category is in the plan)
- Recreate any *missing* channels in that category according to the plan

Use `/protected` to see all protected channels and `/unprotect` to remove protection.

## Project structure

```
├── bot.py                          # Main bot script
├── server-template.json            # Your server plan (gitignored — private)
├── server-template.example.json    # Example plan (commit-friendly)
├── protected-channels.json         # Protected channel IDs (gitignored)
├── .env                            # Token & guild ID (gitignored)
├── .env.example                    # Config template
├── requirements.txt                # Python dependencies
├── .gitignore
├── LICENSE
└── README.md
```

## Security

- The `/setup-server`, `/protect`, `/unprotect`, and `/protected` commands are restricted to server **administrators** only
- `.env`, `server-template.json`, and `protected-channels.json` are gitignored — **never commit them**
- The bot uses only `Intents.default()` — no privileged intents required

## License

MIT
