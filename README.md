# Slack OoO Auto-Responder

Automatically replies to direct messages when your Slack status matches a configured "away" keyword — like an out-of-office email auto-reply, but for Slack.

## How It Works

1. You set a Slack status like `:palm_tree: AI Week in SF - unavailable`
2. Someone DMs you
3. The bot checks your status, sees the keyword **"unavailable"**, and sends an auto-reply
4. The sender is informed you're away and given alternative contact options
5. A cooldown prevents the same person from getting spammed (default: 1 reply per hour)

## Prerequisites

- Python 3.10+
- A Slack workspace where you can install custom apps (or request admin approval)

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** → **From scratch**
2. Name it something like `OoO Bot` and select your workspace

### 2. Enable Socket Mode

1. In your app settings, go to **Socket Mode** (left sidebar)
2. Toggle **Enable Socket Mode** to ON
3. You'll be prompted to create an **App-Level Token** — name it `socket-token` and add the `connections:write` scope
4. Copy the `xapp-...` token — this is your `SLACK_APP_TOKEN`

### 3. Configure Event Subscriptions

1. Go to **Event Subscriptions** (left sidebar) and toggle ON
2. Under **Subscribe to bot events**, add:
   - `message.im`
3. Save changes

### 4. Set OAuth Scopes

1. Go to **OAuth & Permissions** (left sidebar)
2. Under **Bot Token Scopes**, add:
   - `chat:write` — send auto-replies
   - `im:history` — receive DM events
   - `im:read` — access DM metadata
   - `users.profile:read` — read your status
3. Scroll up and click **Install to Workspace** (or **Request to Install** if admin approval is required)
4. Copy the `xoxb-...` token — this is your `SLACK_BOT_TOKEN`

### 5. Find Your Member ID

1. In Slack, click your profile picture (top-right)
2. Click **Profile**
3. Click the **⋯** (more) button
4. Click **Copy member ID**

### 6. Configure the Bot

```bash
cd slack-ooo-bot
cp .env.example .env
```

Edit `.env` and fill in your three values:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
OWNER_USER_ID=U0XXXXXXXXX
```

### 7. Install and Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

You should see:

```
INFO:ooo-bot:Starting OoO bot for user U0XXXXXXXXX
INFO:ooo-bot:Trigger keywords: ['unavailable', 'out of office', 'ooo', ...]
⚡️ Bolt app is running!
```

### 8. Important — Allow DMs to the Bot

For the bot to receive DM events, the bot needs to be part of the conversation. This happens automatically when:
- Someone DMs **you** (not the bot) — the bot receives the event via the `message.im` subscription on your behalf

**However**, the bot sends its reply as itself. The first time, Slack may prompt you to allow the app to message in your DMs. Make sure to accept this.

## Configuration

Edit `config.py` to customize:

| Setting | Description | Default |
|---|---|---|
| `STATUS_TRIGGERS` | Keywords in your status that activate the bot | `["unavailable", "out of office", "ooo", "on leave", "vacation", "do not disturb"]` |
| `REPLY_TEMPLATE` | The auto-reply message (`{status_text}` is replaced with your actual status) | See `config.py` |
| `COOLDOWN_SECONDS` | Min seconds between replies to the same person | `3600` (1 hour) |

## Example Auto-Reply

When someone DMs you while your status is `:palm_tree: AI Week in SF - unavailable`, they'll see:

> **OoO Bot** `APP`
>
> Thanks for reaching out to GG. As per his Slack status, he is currently *AI Week in SF - unavailable*.
>
> He will get back to you as soon as possible. Should your question be urgent, please either message your TSM or submit a support ticket.

## Stopping the Bot

Press `Ctrl+C` in the terminal, or remove your "away" status — the bot only replies when your status matches a trigger keyword.
