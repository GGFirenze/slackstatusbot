import os
from dotenv import load_dotenv

load_dotenv()

# Your Slack user ID (Profile → "..." → "Copy member ID")
OWNER_USER_ID = os.environ.get("OWNER_USER_ID", "")

# Reply template — placeholders:
#   {first_name}  → owner's first name from Slack profile
#   {status_text} → owner's current Slack status text
REPLY_TEMPLATE = (
    "Thanks for reaching out to {first_name}. "
    "{first_name}'s Slack status says _{status_text}_. "
    "This person is currently unavailable and will get back to you "
    "as soon as possible.\n\n"
    "Should your question be urgent, please either message your TSM "
    "or submit a support ticket."
)

# Fallback if no Slack status is set when someone DMs you
FALLBACK_STATUS = "unavailable"

# Minimum seconds between auto-replies to the same person
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "3600"))
