import os
import time
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from dotenv import load_dotenv

from config import OWNER_USER_ID, DEFAULT_AWAY_MESSAGE, REPLY_TEMPLATE, COOLDOWN_SECONDS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ooo-bot")

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# User token client — used to post replies in the original DM conversation
user_client = WebClient(token=os.environ["SLACK_USER_TOKEN"])

# Bot state
_active: bool = False
_custom_message: str = DEFAULT_AWAY_MESSAGE

# {sender_user_id: last_reply_unix_timestamp}
_cooldowns: dict[str, float] = {}


def is_on_cooldown(sender_id: str) -> bool:
    last_reply = _cooldowns.get(sender_id)
    if last_reply is None:
        return False
    return (time.time() - last_reply) < COOLDOWN_SECONDS


@app.command("/ooo-on")
def handle_ooo_on(ack, respond, command):
    global _active, _custom_message, _cooldowns
    ack()

    if command.get("user_id") != OWNER_USER_ID:
        respond("Sorry, only GG can control this bot.")
        return

    _active = True
    _cooldowns = {}
    custom = command.get("text", "").strip()
    _custom_message = custom if custom else DEFAULT_AWAY_MESSAGE

    respond(f"Auto-reply *activated*.\nMessage: _{_custom_message}_")
    logger.info("OoO activated with message: %s", _custom_message)


@app.command("/ooo-off")
def handle_ooo_off(ack, respond, command):
    global _active, _cooldowns
    ack()

    if command.get("user_id") != OWNER_USER_ID:
        respond("Sorry, only GG can control this bot.")
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

    reply = REPLY_TEMPLATE.format(message=_custom_message)

    try:
        # Post in the original DM using the user token so the reply
        # appears in the same conversation, from User 1's profile.
        user_client.chat_postMessage(channel=event["channel"], text=reply)
        _cooldowns[sender_id] = time.time()
        logger.info("Auto-replied to %s", sender_id)
    except Exception:
        logger.exception("Failed to send auto-reply to %s", sender_id)


if __name__ == "__main__":
    if not OWNER_USER_ID:
        raise SystemExit("OWNER_USER_ID is not set. Add it to your .env file.")

    logger.info("Starting OoO bot for user %s", OWNER_USER_ID)
    logger.info("Default away message: %s", DEFAULT_AWAY_MESSAGE)
    logger.info("Cooldown: %s seconds", COOLDOWN_SECONDS)

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
