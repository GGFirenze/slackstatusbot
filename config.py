import os
from dotenv import load_dotenv

load_dotenv()

# Your Slack user ID (Profile → "..." → "Copy member ID")
OWNER_USER_ID = os.environ.get("OWNER_USER_ID", "")

# Any status containing one of these substrings (case-insensitive) triggers the auto-reply
STATUS_TRIGGERS = [
    "unavailable",
    "out of office",
    "ooo",
    "on leave",
    "vacation",
    "do not disturb",
]

# Reply template — {status_text} is replaced with your actual Slack status
REPLY_TEMPLATE = (
    "Thanks for reaching out to GG. "
    "As per his Slack status, he is currently _{status_text}_.\n\n"
    "He will get back to you as soon as possible. "
    "Should your question be urgent, please either message your TSM "
    "or submit a support ticket."
)

# Minimum seconds between auto-replies to the same person
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "3600"))
