# Slack OoO Auto-Responder

Automatically replies to direct messages when activated with a slash command — like an out-of-office email auto-reply, but for Slack.

## The Problem

When you set a Slack status like "AI Week in SF - unavailable", people still message you and expect a response. There's no built-in way to auto-reply to DMs the way email handles out-of-office.

## The Solution

A lightweight Slack app that:
- Activates with `/ooo-on` and deactivates with `/ooo-off`
- Automatically replies to any DM you receive while active
- Sends the reply in the original conversation, from your profile
- Only replies once per sender per hour to avoid spam
- Supports custom away messages

## Commands

| Command | Description |
|---|---|
| `/ooo-on` | Activate auto-reply with the default away message |
| `/ooo-on <message>` | Activate with a custom away message (e.g. `/ooo-on At AI Week in SF - back Monday`) |
| `/ooo-off` | Deactivate auto-reply |

All command responses are **ephemeral** — only visible to you.

## Example Auto-Reply

After typing `/ooo-on At AI Week in SF - back Monday`, anyone who DMs you will see this in the conversation:

> Thanks for reaching out to GG. He is At AI Week in SF - back Monday and will get back to you as soon as possible.
>
> Should your question be urgent, please either message your TSM or submit a support ticket.

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│  You type    │    │                  │    │  Sender DMs │
│  /ooo-on     │───▶│  Bot process     │◀───│  you        │
│  in Slack    │    │  (Python + Bolt) │    │             │
└─────────────┘    │                  │    └─────────────┘
                   │  Socket Mode     │
                   │  (WebSocket, no  │───▶ Auto-reply in
                   │   public URL)    │    the same DM
                   └──────────────────┘
```

- **Socket Mode**: The app connects to Slack over WebSocket. No public URL, no firewall changes, no webhook endpoints needed.
- **Single process**: One Python script (`app.py`), ~100 lines of code.
- **Stateless**: All state (on/off, cooldowns) is in memory. A restart resets the bot to "off".

---

## For IT / Workspace Admins

### What this app needs to be approved and deployed

#### Slack App Scopes (minimal, no admin-level access)

**Bot Token Scopes:**

| Scope | Why |
|---|---|
| `chat:write` | Send auto-reply messages |
| `commands` | Handle `/ooo-on` and `/ooo-off` slash commands |
| `im:history` | Receive DM message events the bot is added to |
| `im:read` | Access DM channel metadata |
| `im:write` | Open DM conversations for replies |
| `users.profile:read` | Read user profile details |

**User Token Scopes:**

| Scope | Why |
|---|---|
| `im:history` | Receive DM events on behalf of the user |
| `chat:write` | Post the auto-reply in the user's DM conversation |

#### Event Subscriptions

| Event | Type | Why |
|---|---|---|
| `message.im` | Bot event | Receive direct message events |
| `message.im` | User event | Receive DMs sent to the authorizing user |

#### Slash Commands

| Command | Description |
|---|---|
| `/ooo-on` | Activate out-of-office auto-reply |
| `/ooo-off` | Deactivate out-of-office auto-reply |

#### Security Notes

- The app **does not read message content** — it only detects that a DM was received and replies with a fixed template.
- The app **does not store any data** — cooldowns are in memory and cleared on restart.
- The app uses **Socket Mode** — it connects outbound to Slack over WebSocket. No inbound ports, no public endpoints, no firewall changes needed.
- The app **only responds to DMs** — it does not access channels, groups, or any other conversations.
- Only the configured user (by member ID) can activate/deactivate the auto-reply.

### Deployment

The bot is a single long-running Python process. It needs to be running 24/7 for the slash commands to work.

**Requirements:**
- Python 3.10+
- ~50MB RAM
- No public URL or inbound network access needed

**Environment variables (4 total):**

```
SLACK_BOT_TOKEN=xoxb-...       # Bot User OAuth Token
SLACK_APP_TOKEN=xapp-...       # App-Level Token (Socket Mode)
SLACK_USER_TOKEN=xoxp-...      # User OAuth Token
OWNER_USER_ID=U0XXXXXXXXX      # Slack member ID of the user
```

**Run:**

```bash
pip install -r requirements.txt
python app.py
```

**Docker (optional):**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

The app can be deployed on any platform that supports long-running processes: a VM, a container, Kubernetes, Railway, Render, Fly.io, etc.

---

## Local Development Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it and select your workspace

### 2. Enable Socket Mode

1. Go to **Socket Mode** (left sidebar) → toggle ON
2. Create an **App-Level Token** named `socket-token` with the `connections:write` scope
3. Copy the `xapp-...` token

### 3. Create Slash Commands

1. Go to **Slash Commands** → **Create New Command**:
   - **Command**: `/ooo-on` | **Description**: `Activate out-of-office auto-reply` | **Usage Hint**: `[custom away message]`
2. **Create New Command** again:
   - **Command**: `/ooo-off` | **Description**: `Deactivate out-of-office auto-reply`

### 4. Configure Event Subscriptions

1. Go to **Event Subscriptions** → toggle ON
2. Under **Subscribe to bot events**, add: `message.im`
3. Under **Subscribe to events on behalf of users**, add: `message.im`

### 5. Set OAuth Scopes

1. Go to **OAuth & Permissions**
2. **Bot Token Scopes**: `chat:write`, `commands`, `im:history`, `im:read`, `im:write`, `users.profile:read`
3. **User Token Scopes**: `im:history`, `chat:write`

### 6. Install to Workspace

1. Click **Install to Workspace** and authorize
2. Copy the **Bot User OAuth Token** (`xoxb-...`)
3. Copy the **User OAuth Token** (`xoxp-...`)

### 7. Find Your Member ID

1. In Slack → click your profile → **Profile** → **⋯** → **Copy member ID**

### 8. Configure and Run

```bash
cp .env.example .env
# Fill in your 4 tokens/values in .env

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Configuration

Edit `config.py` to customize:

| Setting | Description | Default |
|---|---|---|
| `DEFAULT_AWAY_MESSAGE` | Away reason when `/ooo-on` is used without a custom message | `"currently unavailable"` |
| `REPLY_TEMPLATE` | The auto-reply message (`{message}` is replaced with the away reason) | See `config.py` |
| `COOLDOWN_SECONDS` | Min seconds between replies to the same person (env: `COOLDOWN_SECONDS`) | `3600` (1 hour) |
