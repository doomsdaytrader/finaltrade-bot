import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROUP_ID = os.environ.get("GROUP_ID", "")

# Topic IDs - User will update these once topics are created
TOPIC_MARKET = os.environ.get("TOPIC_MARKET", "0")
TOPIC_SIGNALS = os.environ.get("TOPIC_SIGNALS", "0")
TOPIC_NEWS = os.environ.get("TOPIC_NEWS", "0")
TOPIC_SURVIVAL = os.environ.get("TOPIC_SURVIVAL", "0")
