import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# Coin mapping: display_name -> (coingecko_id, symbol, emoji, color_emoji)
COIN_MAP = {
    "bitcoin":      ("bitcoin",      "BTC",  "🟠", "₿"),
    "ethereum":     ("ethereum",     "ETH",  "🔷", "Ξ"),
    "solana":       ("solana",       "SOL",  "🟣", "◎"),
    "binancecoin":  ("binancecoin",  "BNB",  "🟡", "⬡"),
    "lunc":         ("terra-luna",   "LUNC", "🔵", "🌙"),
    "ustc":         ("terrausd",     "USTC", "🟢", "💲"),
    "xrp":          ("ripple",       "XRP",  "⚪", "✕"),
    "cardano":      ("cardano",      "ADA",  "🔵", "♦"),
    "dogecoin":     ("dogecoin",     "DOGE", "🟤", "Ð"),
}

# CoinGecko logo URLs (large)
COIN_LOGOS = {
    "bitcoin": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
    "ethereum": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
    "solana": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
    "binancecoin": "https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png",
    "lunc": "https://assets.coingecko.com/coins/images/8284/large/01_LussEJ.png",
    "ustc": "https://assets.coingecko.com/coins/images/12681/large/UST.png",
    "xrp": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png",
    "cardano": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
    "dogecoin": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
}

def _resolve_coin(user_input: str):
    """Resolve user input to a coin entry. Handles aliases like 'btc', 'lunc', etc."""
    user_input = user_input.lower().strip()
    # Direct match
    if user_input in COIN_MAP:
        return user_input, COIN_MAP[user_input]
    # Symbol match
    for key, (cg_id, symbol, emoji, color) in COIN_MAP.items():
        if user_input == symbol.lower() or user_input == cg_id.lower():
            return key, COIN_MAP[key]
    # Fallback: treat as CoinGecko ID directly
    return user_input, (user_input, user_input.upper(), "📊", "•")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "✝️ <b>Welcome to The Final Trade</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🙏 <i>All glory goes to God for this community.</i>\n\n"
        "I am your <b>automated intelligence hub</b>.\n"
        "I provide live data for:\n\n"
        "🟠 <b>Crypto & Finance</b>\n"
        "🌍 <b>Survival & Geopolitics</b>\n"
        "🐋 <b>Whale Tracking</b>\n"
        "🔥 <b>LUNC / USTC Intel</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Commands:</b>\n\n"
        "/price &lt;coin&gt; — Live crypto price\n"
        "/markets — Top market overview\n"
        "/lunc — LUNC (Luna Classic) intel\n"
        "/ustc — USTC (Terra Classic) intel\n"
        "/news — Latest crypto headlines\n"
        "/survival — Geopolitics & Survival\n"
        "/dashboard — Open the Mini App Terminal\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>The Final Trade</b> — powered by faith & data."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = (
            "📊 <b>Usage:</b> <code>/price bitcoin</code>\n\n"
            "🟠 BTC  🔷 ETH  🟣 SOL  🟡 BNB\n"
            "🔵 LUNC  🟢 USTC  ⚪ XRP  🟤 DOGE"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    user_input = context.args[0]
    key, (cg_id, symbol, emoji, color_emoji) = _resolve_coin(user_input)

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}?localization=false&tickers=false&community_data=false&developer_data=false"
        data = requests.get(url, timeout=10).json()

        price = data["market_data"]["current_price"]["usd"]
        change_24h = data["market_data"]["price_change_percentage_24h"] or 0
        market_cap = data["market_data"]["market_cap"]["usd"] or 0
        volume = data["market_data"]["total_volume"]["usd"] or 0
        name = data.get("name", symbol)
        image_url = data.get("image", {}).get("large", "")

        # Format numbers
        if price >= 1:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:,.6f}"

        mc_str = f"${market_cap/1e9:,.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:,.1f}M"
        vol_str = f"${volume/1e9:,.2f}B" if volume >= 1e9 else f"${volume/1e6:,.1f}M"

        # Direction arrow
        if change_24h > 0:
            arrow = "🟢 ▲"
            trend = "BULLISH"
        elif change_24h < 0:
            arrow = "🔴 ▼"
            trend = "BEARISH"
        else:
            arrow = "⚪ ▬"
            trend = "NEUTRAL"

        caption = (
            f"{emoji} <b>{name} ({symbol})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> {price_str}\n"
            f"{arrow} <b>24h:</b> {change_24h:+.2f}%  —  {trend}\n"
            f"📊 <b>Market Cap:</b> {mc_str}\n"
            f"📈 <b>Volume:</b> {vol_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>The Final Trade — All glory to God</i>"
        )

        if image_url:
            await update.message.reply_photo(photo=image_url, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching <b>{user_input}</b>. Check spelling or try again.\n\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


async def markets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top market overview with all tracked coins."""
    coins_to_fetch = ["bitcoin", "ethereum", "solana", "binancecoin", "terra-luna", "terrausd", "ripple", "dogecoin"]
    coin_ids = ",".join(coins_to_fetch)

    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        lines = ["🌐 <b>MARKET OVERVIEW</b>", "━━━━━━━━━━━━━━━━━━━━━━━", ""]

        display_order = [
            ("bitcoin", "BTC", "🟠"),
            ("ethereum", "ETH", "🔷"),
            ("solana", "SOL", "🟣"),
            ("binancecoin", "BNB", "🟡"),
            ("terra-luna", "LUNC", "🔵"),
            ("terrausd", "USTC", "🟢"),
            ("ripple", "XRP", "⚪"),
            ("dogecoin", "DOGE", "🟤"),
        ]

        for cg_id, symbol, emoji in display_order:
            if cg_id in data:
                price = data[cg_id]["usd"]
                change = data[cg_id].get("usd_24h_change", 0) or 0
                arrow = "🟢▲" if change > 0 else "🔴▼" if change < 0 else "⚪▬"

                if price >= 1:
                    p_str = f"${price:,.2f}"
                else:
                    p_str = f"${price:,.6f}"

                lines.append(f"{emoji} <b>{symbol}</b>  {p_str}  {arrow} {change:+.1f}%")

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚡ <i>The Final Trade — All glory to God</i>")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error loading markets.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import feedparser
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        entries = feed.entries[:5]

        lines = ["📰 <b>CRYPTO NEWS — LIVE FEED</b>", "━━━━━━━━━━━━━━━━━━━━━━━", ""]

        for i, entry in enumerate(entries):
            lines.append(f"🔹 <a href='{entry.link}'>{entry.title}</a>")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚡ <i>The Final Trade — All glory to God</i>")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error loading news.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


async def survival_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import feedparser
    try:
        feeds = [
            ("Reuters World", "https://www.reuters.com/world/rss"),
            ("AP News", "https://apnews.com/hub/ap-top-news?output=rss"),
        ]

        lines = ["🌍 <b>SURVIVAL & GEOPOLITICS — LIVE INTEL</b>", "━━━━━━━━━━━━━━━━━━━━━━━", ""]

        for source_name, rss_url in feeds:
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:3]:
                    lines.append(f"🔸 <a href='{entry.link}'>{entry.title}</a>")
                    lines.append(f"   <i>— {source_name}</i>")
                    lines.append("")
            except:
                pass

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚡ <i>The Final Trade — All glory to God</i>")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error loading survival intel.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🖥️ <b>THE FINAL TRADE TERMINAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Access the full cyberpunk dashboard:\n\n"
        "🌐 <a href='https://finaltrade-dashboard-91me6lozz-irayecrypto-1565s-projects.vercel.app'>OPEN TERMINAL</a>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>The Final Trade — All glory to God</i>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=False)


async def lunc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dedicated LUNC (Luna Classic) command with detailed intel."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/terra-luna?localization=false&tickers=false&community_data=false&developer_data=false"
        data = requests.get(url, timeout=10).json()

        price = data["market_data"]["current_price"]["usd"]
        change_24h = data["market_data"]["price_change_percentage_24h"] or 0
        change_7d = data["market_data"]["price_change_percentage_7d"] or 0
        market_cap = data["market_data"]["market_cap"]["usd"] or 0
        volume = data["market_data"]["total_volume"]["usd"] or 0
        circulating = data["market_data"]["circulating_supply"] or 0
        image_url = data.get("image", {}).get("large", "")

        arrow_24h = "🟢▲" if change_24h > 0 else "🔴▼"
        arrow_7d = "🟢▲" if change_7d > 0 else "🔴▼"

        caption = (
            f"🔵🌙 <b>LUNC — LUNA CLASSIC</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> ${price:,.6f}\n"
            f"{arrow_24h} <b>24h Change:</b> {change_24h:+.2f}%\n"
            f"{arrow_7d} <b>7d Change:</b> {change_7d:+.2f}%\n"
            f"📊 <b>Market Cap:</b> ${market_cap/1e6:,.1f}M\n"
            f"📈 <b>24h Volume:</b> ${volume/1e6:,.1f}M\n"
            f"🔄 <b>Circulating:</b> {circulating/1e9:,.1f}B LUNC\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>BURN THE SUPPLY. REBUILD THE ECOSYSTEM.</b>\n"
            f"⚡ <i>The Final Trade — All glory to God</i>"
        )

        if image_url:
            await update.message.reply_photo(photo=image_url, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching LUNC data.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


async def ustc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dedicated USTC (TerraClassicUSD) command with detailed intel."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/terrausd?localization=false&tickers=false&community_data=false&developer_data=false"
        data = requests.get(url, timeout=10).json()

        price = data["market_data"]["current_price"]["usd"]
        change_24h = data["market_data"]["price_change_percentage_24h"] or 0
        change_7d = data["market_data"]["price_change_percentage_7d"] or 0
        market_cap = data["market_data"]["market_cap"]["usd"] or 0
        volume = data["market_data"]["total_volume"]["usd"] or 0
        image_url = data.get("image", {}).get("large", "")

        arrow_24h = "🟢▲" if change_24h > 0 else "🔴▼"
        arrow_7d = "🟢▲" if change_7d > 0 else "🔴▼"

        # Calculate repeg distance
        repeg_distance = abs(1.0 - price) / 1.0 * 100

        caption = (
            f"🟢💲 <b>USTC — TERRA CLASSIC USD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> ${price:,.6f}\n"
            f"{arrow_24h} <b>24h Change:</b> {change_24h:+.2f}%\n"
            f"{arrow_7d} <b>7d Change:</b> {change_7d:+.2f}%\n"
            f"📊 <b>Market Cap:</b> ${market_cap/1e6:,.1f}M\n"
            f"📈 <b>24h Volume:</b> ${volume/1e6:,.1f}M\n"
            f"🎯 <b>Re-peg Distance:</b> {repeg_distance:.2f}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>TARGET: $1.00 RE-PEG</b>\n"
            f"⚡ <i>The Final Trade — All glory to God</i>"
        )

        if image_url:
            await update.message.reply_photo(photo=image_url, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching USTC data.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)
