import os
import time
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from dotenv import load_dotenv

from config import OWNER_USER_ID, REPLY_TEMPLATE, FALLBACK_STATUS, COOLDOWN_SECONDS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ooo-bot")

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# User token client — posts replies in the original DM conversation
user_client = WebClient(token=os.environ["SLACK_USER_TOKEN"])

# Bot state
_active: bool = False

# {sender_user_id: last_reply_unix_timestamp}
_cooldowns: dict[str, float] = {}


def get_owner_profile(client) -> tuple[str, str]:
    """Fetch the owner's first name and current status text."""
    try:
        resp = client.users_profile_get(user=OWNER_USER_ID)
        profile = resp.get("profile", {})
        first_name = profile.get("first_name") or profile.get("real_name", "")
        status_text = profile.get("status_text", "") or FALLBACK_STATUS
        return first_name, status_text
    except Exception:
        logger.exception("Failed to fetch owner profile")
        return "", FALLBACK_STATUS


def is_on_cooldown(sender_id: str) -> bool:
    last_reply = _cooldowns.get(sender_id)
    if last_reply is None:
        return False
    return (time.time() - last_reply) < COOLDOWN_SECONDS


@app.command("/ooo-on")
def handle_ooo_on(ack, respond, command):
    global _active, _cooldowns
    ack()

    if command.get("user_id") != OWNER_USER_ID:
        respond("Sorry, only the bot owner can control this.")
        return

    _active = True
    _cooldowns = {}

    first_name, status_text = get_owner_profile(app.client)
    respond(
        f"Auto-reply *activated*.\n"
        f"Your current status: _{status_text}_\n"
        f"Replies will use your name: _{first_name}_"
    )
    logger.info("OoO activated")


@app.command("/ooo-off")
def handle_ooo_off(ack, respond, command):
    global _active, _cooldowns
    ack()

    if command.get("user_id") != OWNER_USER_ID:
        respond("Sorry, only the bot owner can control this.")
        return

    _active = False
    _cooldowns = {}

    respond("Auto-reply *deactivated*.")
    logger.info("OoO deactivated")


@app.event("message")
def handle_message(event, client):
    if not _active:
        return

    if event.get("channel_type") != "im":
        return

    if event.get("subtype") or event.get("bot_id"):
        return

    sender_id = event.get("user")
    if not sender_id or sender_id == OWNER_USER_ID:
        return

    if is_on_cooldown(sender_id):
        logger.debug("Skipping %s (on cooldown)", sender_id)
        return

    first_name, status_text = get_owner_profile(client)
    reply = REPLY_TEMPLATE.format(first_name=first_name, status_text=status_text)

    try:
        user_client.chat_postMessage(channel=event["channel"], text=reply)
        _cooldowns[sender_id] = time.time()
        logger.info("Auto-replied to %s (status: %s)", sender_id, status_text)
    except Exception:
        logger.exception("Failed to send auto-reply to %s", sender_id)


if __name__ == "__main__":
    if not OWNER_USER_ID:
        raise SystemExit("OWNER_USER_ID is not set. Add it to your .env file.")

    logger.info("Starting OoO bot for user %s", OWNER_USER_ID)
    logger.info("Cooldown: %s seconds", COOLDOWN_SECONDS)

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
