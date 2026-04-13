import os
import time
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

from config import OWNER_USER_ID, STATUS_TRIGGERS, REPLY_TEMPLATE, COOLDOWN_SECONDS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ooo-bot")

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# {sender_user_id: last_reply_unix_timestamp}
_cooldowns: dict[str, float] = {}


def get_triggered_status(client) -> str | None:
    """Return the owner's status_text if it matches a trigger keyword, else None."""
    try:
        resp = client.users_profile_get(user=OWNER_USER_ID)
    except Exception:
        logger.exception("Failed to fetch owner profile")
        return None

    status_text = resp.get("profile", {}).get("status_text", "")
    if not status_text:
        return None

    status_lower = status_text.lower()
    for trigger in STATUS_TRIGGERS:
        if trigger.lower() in status_lower:
            return status_text

    return None


def is_on_cooldown(sender_id: str) -> bool:
    last_reply = _cooldowns.get(sender_id)
    if last_reply is None:
        return False
    return (time.time() - last_reply) < COOLDOWN_SECONDS


@app.event("message")
def handle_message(event, client):
    if event.get("channel_type") != "im":
        return

    # Ignore bot messages, edits, deletions, and other subtypes
    if event.get("subtype") or event.get("bot_id"):
        return

    sender_id = event.get("user")
    if not sender_id or sender_id == OWNER_USER_ID:
        return

    if is_on_cooldown(sender_id):
        logger.debug("Skipping %s (on cooldown)", sender_id)
        return

    status_text = get_triggered_status(client)
    if not status_text:
        return

    reply = REPLY_TEMPLATE.format(status_text=status_text)

    try:
        client.chat_postMessage(channel=event["channel"], text=reply)
        _cooldowns[sender_id] = time.time()
        logger.info("Auto-replied to %s (status: %s)", sender_id, status_text)
    except Exception:
        logger.exception("Failed to send auto-reply to %s", sender_id)


if __name__ == "__main__":
    if not OWNER_USER_ID:
        raise SystemExit("OWNER_USER_ID is not set. Add it to your .env file.")

    logger.info("Starting OoO bot for user %s", OWNER_USER_ID)
    logger.info("Trigger keywords: %s", STATUS_TRIGGERS)
    logger.info("Cooldown: %s seconds", COOLDOWN_SECONDS)

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
