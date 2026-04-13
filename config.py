import os
from dotenv import load_dotenv

load_dotenv()

# Your Slack user ID (Profile → "..." → "Copy member ID")
OWNER_USER_ID = os.environ.get("OWNER_USER_ID", "")

# Default away message used when /ooo-on is called without a custom message
DEFAULT_AWAY_MESSAGE = "currently unavailable"

# Reply template — {message} is replaced with the away reason
REPLY_TEMPLATE = (
    "Thanks for reaching out to GG. "
    "He is {message} and will get back to you as soon as possible.\n\n"
    "Should your question be urgent, please either message your TSM "
    "or submit a support ticket."
)

# Minimum seconds between auto-replies to the same person
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "3600"))
