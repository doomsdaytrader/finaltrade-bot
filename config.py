import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROUP_ID = os.environ.get("GROUP_ID", "")

# WEEX Referral
WEEX_REF = "t4fl"

# Wallets for Premium (from your existing setup)
TRC20_WALLET = os.environ.get("TRC20_WALLET", "")
BTC_WALLET = os.environ.get("BTC_WALLET", "")
ETH_WALLET = os.environ.get("ETH_WALLET", "")

# Topic IDs for Supergroup auto-posting
TOPIC_MARKET = os.environ.get("TOPIC_MARKET", "0")
TOPIC_SIGNALS = os.environ.get("TOPIC_SIGNALS", "0")
TOPIC_NEWS = os.environ.get("TOPIC_NEWS", "0")
TOPIC_SURVIVAL = os.environ.get("TOPIC_SURVIVAL", "0")

# CoinGecko API URLs
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&sparkline=true&price_change_percentage=1h,24h"
COINGECKO_COIN = "https://api.coingecko.com/api/v3/coins/{}"
FEAR_GREED_API = "https://api.alternative.me/fng/?limit=1"

# RSS Feeds — Crypto + World + Science + Survival
NEWS_FEEDS = {
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://cryptoslate.com/feed/",
    ],
    "world": [
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.reutersagency.com/feed/?best-topics=politics&post_type=best",
    ],
    "science": [
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "https://www.space.com/feeds/all",
    ],
    "survival": [
        "https://www.noaa.gov/news.rss",
    ],
}

# Category display config
CATEGORY_CONFIG = {
    "crypto": {"emoji": "📰", "label": "CRYPTO INTEL", "color": "🟠"},
    "world": {"emoji": "🌍", "label": "WORLD NEWS", "color": "🔵"},
    "science": {"emoji": "🔬", "label": "SCIENCE & SPACE", "color": "🟣"},
    "survival": {"emoji": "🛡️", "label": "SURVIVAL ALERT", "color": "🔴"},
}
