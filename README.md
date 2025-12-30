# Ichiro Commission Discord Bot

A Discord bot built with `discord.py` that posts mini announcements, tracks reactions, retrieves signups, and builds team layouts.

## Prerequisites
- Python 3.12+
- A Discord account with permission to create/manage applications

## Create your bot in the Discord Developer Portal
1. Go to https://discord.com/developers/applications and click **New Application**.
2. Name it and create.
3. In **Bot** tab:
   - Click **Add Bot**.
   - Copy the **Token** (you’ll place it in `config.yml` later).
   - Turn **Message Content Intent**, **Server Members Intent**, and **Presence Intent** ON.
4. In **OAuth2 → URL Generator**:
   - Scopes: select **bot** and **application.commands**.
   - Bot permissions: select **Administrator** (or the minimum set you prefer; admin is the quickest for setup).
   - Copy the generated URL and open it to invite the bot to your server.

## Configure the bot
Update `config.yml`:
```yaml
General:
    TOKEN: "YOUR_BOT_TOKEN_HERE"
    ACTIVITY: "watching"          # playing | watching | listening | streaming
    DOING_ACTIVITY: "Minis"
    STREAMING_ACTIVITY_TWITCH_URL: ""
    STATUS: "online"              # online | idle | dnd | invisible
    EMBED_COLOR: "#9C27B0"
    GUILD_ID: 123456789012345678  # your server ID

Permissions:
    COMMAND_ROLES: []             # role IDs allowed to run commands; leave empty to allow all
```

## Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Run the bot
```bash
python3 main.py
```

On startup, commands sync to the configured `GUILD_ID`. Make sure the bot is invited and online.

## Key commands
- `/mini` — post a mini announcement with a ✅ reaction and time-stamped start.
- `/retrieve` — send the list of reactors to a channel and log unreacts after retrieval.
- `/teams` — build team layouts with Components v2, including game order, host, and optional role assignment.

## Notes
- The bot uses all intents (`discord.Intents.all()`); ensure they’re enabled in the Developer Portal.
- Admin permission in the invite URL simplifies setup; tighten permissions later if desired.***