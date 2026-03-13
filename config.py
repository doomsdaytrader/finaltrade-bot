import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROUP_ID = os.environ.get("GROUP_ID", "")

# WEEX Referral
WEEX_REF = "t4fl"

# Wallets
TRC20_WALLET = os.environ.get("TRC20_WALLET", "")
BTC_WALLET = os.environ.get("BTC_WALLET", "")
ETH_WALLET = os.environ.get("ETH_WALLET", "")

# Topic IDs for Supergroup
TOPIC_MARKET = os.environ.get("TOPIC_MARKET", "0")
TOPIC_SIGNALS = os.environ.get("TOPIC_SIGNALS", "0")
TOPIC_NEWS = os.environ.get("TOPIC_NEWS", "0")
TOPIC_SURVIVAL = os.environ.get("TOPIC_SURVIVAL", "0")

# APIs
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&sparkline=true&price_change_percentage=1h,24h"
COINGECKO_COIN = "https://api.coingecko.com/api/v3/coins/{}"
FEAR_GREED_API = "https://api.alternative.me/fng/?limit=1"

# ============================================================
# MASSIVE RSS FEED DATABASE
# ============================================================
NEWS_FEEDS = {
    # ---- CRYPTO & FINANCE ----
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://cryptoslate.com/feed/",
        "https://bitcoinmagazine.com/.rss/full/",
        "https://decrypt.co/feed",
    ],
    "finance": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
        "https://feeds.bloomberg.com/markets/news.rss",
    ],

    # ---- WORLD NEWS & GEOPOLITICS ----
    "world": [
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.reutersagency.com/feed/?best-topics=politics&post_type=best",
    ],

    # ---- SURVIVAL / PREPPING / COLLAPSE ----
    "survival": [
        "https://www.noaa.gov/news.rss",
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.atom",
        "https://www.who.int/rss-feeds/news-english.xml",
        "https://www.ready.gov/rss.xml",
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
    ],

    # ---- WAR / CONFLICT / DEFENSE ----
    "conflict": [
        "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
        "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml",
    ],

    # ---- SCIENCE / SPACE / NASA ----
    "science": [
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "https://www.space.com/feeds/all",
        "https://phys.org/rss-feed/space-news/",
    ],

    # ---- ENERGY / ECONOMIC CRISIS ----
    "energy": [
        "https://oilprice.com/rss/main",
        "https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml",
    ],

    # ---- HEALTH / PANDEMIC ----
    "health": [
        "https://www.who.int/rss-feeds/news-english.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://feeds.bbci.co.uk/news/health/rss.xml",
    ],
}

# Category display config with emojis for rich visual posts
CATEGORY_CONFIG = {
    "crypto":   {"emoji": "📰", "label": "CRYPTO INTEL",           "color": "🟠", "hashtag": "#crypto #bitcoin"},
    "finance":  {"emoji": "💹", "label": "FINANCIAL MARKETS",      "color": "💵", "hashtag": "#finance #markets"},
    "world":    {"emoji": "🌍", "label": "WORLD NEWS",             "color": "🔵", "hashtag": "#world #geopolitics"},
    "survival": {"emoji": "🛡️", "label": "SURVIVAL & DISASTER",    "color": "🔴", "hashtag": "#survival #prepping"},
    "conflict": {"emoji": "⚔️", "label": "WAR & CONFLICT",         "color": "🟤", "hashtag": "#conflict #defense"},
    "science":  {"emoji": "🔬", "label": "SCIENCE & SPACE",        "color": "🟣", "hashtag": "#nasa #space"},
    "energy":   {"emoji": "⛽", "label": "ENERGY & RESOURCES",     "color": "🟡", "hashtag": "#energy #oil"},
    "health":   {"emoji": "🏥", "label": "HEALTH & PANDEMIC",      "color": "🟢", "hashtag": "#health #pandemic"},
}
