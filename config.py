import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
GROUP_ID = os.getenv("GROUP_ID", "-100YOUR_GROUP_ID")

# Topic IDs - User will update these once topics are created
TOPIC_MARKET = os.getenv("TOPIC_MARKET", "0")
TOPIC_SIGNALS = os.getenv("TOPIC_SIGNALS", "0")
TOPIC_NEWS = os.getenv("TOPIC_NEWS", "0")
TOPIC_SURVIVAL = os.getenv("TOPIC_SURVIVAL", "0")
