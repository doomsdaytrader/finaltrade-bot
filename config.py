import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROUP_ID = os.environ.get("GROUP_ID", "-1001196364551")  # @ayewaken verified

# Affiliate / Referral Links
BITBASE_REF = "TXNN7S"
WEEX_REF = "t4fl"
BYDFI_REF = "Bz6sDCCX&f=LUNC"
BYBIT_REF = "95997"
BITUNIX_REF = "pumpcity"
KCEX_REF = "ZAWFPO"
VOOX_REF = "QVHTWAEV"
BITMART_REF = "ctYdrc"
ORANGEX_REF = "f9vatgs2"

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
    "crypto":   {"emoji": "ðŸ“°", "label": "CRYPTO INTEL",           "color": "ðŸŸ ", "hashtag": "#crypto #bitcoin"},
    "finance":  {"emoji": "ðŸ’¹", "label": "FINANCIAL MARKETS",      "color": "ðŸ’µ", "hashtag": "#finance #markets"},
    "world":    {"emoji": "ðŸŒ", "label": "WORLD NEWS",             "color": "ðŸ”µ", "hashtag": "#world #geopolitics"},
    "survival": {"emoji": "ðŸ›¡ï¸", "label": "SURVIVAL & DISASTER",    "color": "ðŸ”´", "hashtag": "#survival #prepping"},
    "conflict": {"emoji": "âš”ï¸", "label": "WAR & CONFLICT",         "color": "ðŸŸ¤", "hashtag": "#conflict #defense"},
    "science":  {"emoji": "ðŸ”¬", "label": "SCIENCE & SPACE",        "color": "ðŸŸ£", "hashtag": "#nasa #space"},
    "energy":   {"emoji": "â›½", "label": "ENERGY & RESOURCES",     "color": "ðŸŸ¡", "hashtag": "#energy #oil"},
    "health":   {"emoji": "ðŸ¥", "label": "HEALTH & PANDEMIC",      "color": "ðŸŸ¢", "hashtag": "#health #pandemic"},
}

