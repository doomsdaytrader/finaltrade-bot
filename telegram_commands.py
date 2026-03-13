import requests
import feedparser
from statistics import mean
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import (
    WEEX_REF, TRC20_WALLET, BTC_WALLET, ETH_WALLET,
    COINGECKO_MARKETS, COINGECKO_COIN, FEAR_GREED_API,
    NEWS_FEEDS, CATEGORY_CONFIG
)

# ============================================================
# RSI ESTIMATION (from sparkline data)
# ============================================================
def estimate_rsi(prices):
    """Estimate RSI from a list of price points."""
    gains, losses = [], []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))
    avg_gain = mean(gains) if gains else 0.001
    avg_loss = mean(losses) if losses else 0.001
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


# ============================================================
# AI SIGNAL GENERATOR
# ============================================================
def generate_ai_signal(data):
    """Generate an AI-style trading signal from CoinGecko coin data."""
    price = data['market_data']['current_price']['usd']
    change = data['market_data'].get('price_change_percentage_24h', 0) or 0
    sparkline = data['market_data'].get('sparkline_7d', {}).get('price', [])

    if len(sparkline) >= 14:
        rsi = estimate_rsi(sparkline[-24:])
    else:
        rsi = 50.0

    # RSI interpretation
    if rsi > 70:
        mood = "🔴 OVERBOUGHT — Watch for pullbacks"
        action = "⚠️ Consider taking profits or tightening stops"
    elif rsi < 30:
        mood = "🟢 OVERSOLD — Whale accumulation zone"
        action = "💎 Strong buy signal for patient holders"
    elif rsi > 55:
        mood = "🟡 SLIGHTLY BULLISH — Momentum building"
        action = "📈 Trail stops and ride the wave"
    else:
        mood = "⚪ NEUTRAL — Consolidation phase"
        action = "⏳ Wait for confirmation before entry"

    trend = "✅ Bullish continuation expected" if change > 0 else "⚠️ Bearish pressure detected"

    signal = (
        f"🧠 <b>AI SIGNAL ANALYSIS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 RSI: <b>{rsi}</b> — {mood}\n"
        f"📉 Trend: {trend}\n"
        f"🎯 Action: {action}\n"
        f"⚡ Leverage Zone: 10x-20x for short bursts"
    )
    return signal, rsi


# ============================================================
# FETCH DETAILED COIN DATA
# ============================================================
def fetch_coin_detail(coin_id: str):
    """Fetch full coin data from CoinGecko with sparkline."""
    url = COINGECKO_COIN.format(coin_id)
    params = "?localization=false&tickers=false&community_data=false&developer_data=false&sparkline=true"
    r = requests.get(url + params, timeout=15)
    return r.json()


# ============================================================
# /START COMMAND — Interactive Menu
# ============================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔵 LUNC Signal", callback_data="signal_terra-luna"),
            InlineKeyboardButton("🟢 USTC Signal", callback_data="signal_terrausd"),
        ],
        [
            InlineKeyboardButton("🟠 BTC Forecast", callback_data="signal_bitcoin"),
            InlineKeyboardButton("🔷 ETH Forecast", callback_data="signal_ethereum"),
        ],
        [
            InlineKeyboardButton("📊 Market Overview", callback_data="cmd_markets"),
            InlineKeyboardButton("😱 Fear & Greed", callback_data="cmd_feargreed"),
        ],
        [
            InlineKeyboardButton("📰 Crypto News", callback_data="cmd_news"),
            InlineKeyboardButton("🌍 World News", callback_data="cmd_survival"),
        ],
        [
            InlineKeyboardButton("🔬 NASA & Space", callback_data="cmd_science"),
            InlineKeyboardButton("🔍 Token Scanner", callback_data="cmd_scanner"),
        ],
        [
            InlineKeyboardButton("🖥️ Open Terminal", callback_data="cmd_dashboard"),
            InlineKeyboardButton("⚠️ Disclaimer", callback_data="cmd_disclaimer"),
        ],
    ])

    msg = (
        "✝️ <b>WELCOME TO THE FINAL TRADE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🙏 <i>All glory goes to God.</i>\n\n"
        "🧠 <b>Your AI-Powered Intelligence Hub:</b>\n\n"
        "🔹 LUNC & USTC Deep Metrics + RSI\n"
        "🔹 Auto Signals 24/7 with AI Analysis\n"
        "🔹 World / NASA / NOAA / Geopolitics\n"
        "🔹 RSI, Sparkline, Volume, Whale Zones\n"
        "🔹 WEEX Leverage 10x-30x Alerts\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ Tap any button below to begin."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ============================================================
# CALLBACK HANDLER — Button Presses
# ============================================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("signal_"):
        coin_id = data.replace("signal_", "")
        await _send_full_signal(query.message.chat.id, coin_id, context)
    elif data == "cmd_markets":
        await _send_markets(query.message.chat.id, context)
    elif data == "cmd_feargreed":
        await _send_fear_greed(query.message.chat.id, context)
    elif data == "cmd_news":
        await _send_rss_news(query.message.chat.id, "crypto", context)
    elif data == "cmd_survival":
        await _send_rss_news(query.message.chat.id, "world", context)
    elif data == "cmd_science":
        await _send_rss_news(query.message.chat.id, "science", context)
    elif data == "cmd_scanner":
        await context.bot.send_message(
            query.message.chat.id,
            "🔍 <b>Token Scanner</b>\n\nUse /token followed by any coin:\n<code>/token sol</code>\n<code>/token doge</code>\n<code>/token xrp</code>",
            parse_mode=ParseMode.HTML
        )
    elif data == "cmd_dashboard":
        await _send_dashboard(query.message.chat.id, context)
    elif data == "cmd_disclaimer":
        await context.bot.send_message(
            query.message.chat.id,
            "⚠️ <b>Disclaimer</b>\n\nThis bot is for educational and informational purposes only. "
            "Not financial advice. Always do your own research. Trade at your own risk.\n\n"
            "✝️ <i>All glory to God.</i>",
            parse_mode=ParseMode.HTML
        )


# ============================================================
# FULL SIGNAL — Coin logo + RSI + AI + WEEX link
# ============================================================
async def _send_full_signal(chat_id, coin_id, context):
    try:
        data = fetch_coin_detail(coin_id)
        name = data.get('name', coin_id.upper())
        symbol = data.get('symbol', '').upper()
        price = data['market_data']['current_price']['usd']
        change_24h = data['market_data'].get('price_change_percentage_24h', 0) or 0
        change_7d = data['market_data'].get('price_change_percentage_7d', 0) or 0
        market_cap = data['market_data'].get('market_cap', {}).get('usd', 0) or 0
        volume = data['market_data'].get('total_volume', {}).get('usd', 0) or 0
        image_url = data.get('image', {}).get('large', '')

        ai_signal, rsi = generate_ai_signal(data)

        # Price formatting
        p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
        mc_str = f"${market_cap/1e9:,.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:,.1f}M"
        vol_str = f"${volume/1e9:,.2f}B" if volume >= 1e9 else f"${volume/1e6:,.1f}M"
        arrow_24h = "🟢▲" if change_24h > 0 else "🔴▼"
        arrow_7d = "🟢▲" if change_7d > 0 else "🔴▼"

        weex_link = f"https://www.weex.com/en/spot/{symbol}_USDT?vipCode={WEEX_REF}"

        caption = (
            f"🚨 <b>{name} ({symbol}) — SIGNAL</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> {p_str}\n"
            f"{arrow_24h} <b>24h:</b> {change_24h:+.2f}%\n"
            f"{arrow_7d} <b>7d:</b> {change_7d:+.2f}%\n"
            f"📊 <b>Market Cap:</b> {mc_str}\n"
            f"📈 <b>Volume:</b> {vol_str}\n\n"
            f"{ai_signal}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — All glory to God</i>"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📈 Trade {symbol} on WEEX", url=weex_link)],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="cmd_back")],
        ])

        if image_url:
            await context.bot.send_photo(
                chat_id=chat_id, photo=image_url,
                caption=caption, parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id, text=caption,
                parse_mode=ParseMode.HTML, reply_markup=keyboard
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Error fetching signal for <b>{coin_id}</b>.\n<i>{str(e)[:150]}</i>",
            parse_mode=ParseMode.HTML
        )


# ============================================================
# /PRICE COMMAND
# ============================================================
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = (
            "📊 <b>Usage:</b> <code>/price bitcoin</code>\n\n"
            "🟠 BTC  🔷 ETH  🟣 SOL  🟡 BNB\n"
            "🔵 LUNC  🟢 USTC  ⚪ XRP  🟤 DOGE\n\n"
            "<i>Or use /token for full AI signal analysis</i>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    coin_id = context.args[0].lower()
    # Handle aliases
    aliases = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin",
               "lunc": "terra-luna", "ustc": "terrausd", "xrp": "ripple", "doge": "dogecoin",
               "ada": "cardano", "dot": "polkadot", "avax": "avalanche-2"}
    coin_id = aliases.get(coin_id, coin_id)

    await _send_full_signal(update.message.chat.id, coin_id, context)


# ============================================================
# /TOKEN COMMAND — Scan any coin
# ============================================================
async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔍 <b>Token Scanner</b>\n\nUsage: <code>/token sol</code>",
            parse_mode=ParseMode.HTML
        )
        return
    coin_id = context.args[0].lower()
    aliases = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin",
               "lunc": "terra-luna", "ustc": "terrausd", "xrp": "ripple", "doge": "dogecoin"}
    coin_id = aliases.get(coin_id, coin_id)
    await _send_full_signal(update.message.chat.id, coin_id, context)


# ============================================================
# /MARKETS COMMAND
# ============================================================
async def markets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_markets(update.message.chat.id, context)

async def _send_markets(chat_id, context):
    coins = "bitcoin,ethereum,solana,binancecoin,terra-luna,terrausd,ripple,dogecoin"
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        display = [
            ("bitcoin", "BTC", "🟠"), ("ethereum", "ETH", "🔷"),
            ("solana", "SOL", "🟣"), ("binancecoin", "BNB", "🟡"),
            ("terra-luna", "LUNC", "🔵"), ("terrausd", "USTC", "🟢"),
            ("ripple", "XRP", "⚪"), ("dogecoin", "DOGE", "🟤"),
        ]

        # Fear & Greed
        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            fg_val = fg['value']
            fg_class = fg['value_classification']
            fg_emoji = "😱" if int(fg_val) < 25 else "😰" if int(fg_val) < 50 else "😐" if int(fg_val) < 75 else "🤑"
            fg_text = f"\n{fg_emoji} <b>Fear & Greed Index:</b> {fg_val} — {fg_class}\n"
        except:
            pass

        lines = ["🌐 <b>MARKET OVERVIEW — THE FINAL TRADE</b>", "━━━━━━━━━━━━━━━━━━━━━━━", fg_text]

        for cg_id, symbol, emoji in display:
            if cg_id in data:
                price = data[cg_id]["usd"]
                change = data[cg_id].get("usd_24h_change", 0) or 0
                arrow = "🟢▲" if change > 0 else "🔴▼" if change < 0 else "⚪▬"
                p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
                lines.append(f"{emoji} <b>{symbol}</b>  {p_str}  {arrow} {change:+.1f}%")

        lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━", "✝️ <i>The Final Trade — All glory to God</i>"])
        await context.bot.send_message(chat_id, "\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error loading markets.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# FEAR & GREED
# ============================================================
async def _send_fear_greed(chat_id, context):
    try:
        fg = requests.get(FEAR_GREED_API, timeout=10).json()['data'][0]
        val = int(fg['value'])
        classification = fg['value_classification']

        if val < 25:
            bar = "🔴🔴🔴🔴🔴⚪⚪⚪⚪⚪"
            emoji = "😱"
            insight = "Extreme fear — historically a strong buying opportunity"
        elif val < 50:
            bar = "🟠🟠🟠🟠🟠⚪⚪⚪⚪⚪"
            emoji = "😰"
            insight = "Fear in the market — smart money is watching closely"
        elif val < 75:
            bar = "🟡🟡🟡🟡🟡🟡🟡⚪⚪⚪"
            emoji = "😐"
            insight = "Neutral to greedy — market is building confidence"
        else:
            bar = "🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢"
            emoji = "🤑"
            insight = "Extreme greed — caution! Tops often form here"

        msg = (
            f"{emoji} <b>FEAR & GREED INDEX</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 <b>Score:</b> {val}/100\n"
            f"📈 <b>Status:</b> {classification}\n"
            f"{bar}\n\n"
            f"💡 <b>Insight:</b> {insight}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — All glory to God</i>"
        )
        await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error fetching Fear & Greed.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# /NEWS, /SURVIVAL, /SCIENCE COMMANDS — RSS Feeds
# ============================================================
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "crypto", context)

async def survival_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "world", context)

async def science_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "science", context)

async def _send_rss_news(chat_id, category, context):
    try:
        config = CATEGORY_CONFIG.get(category, {"emoji": "📰", "label": category.upper(), "color": "⚪"})
        feeds = NEWS_FEEDS.get(category, [])
        entries = []

        for rss_url in feeds:
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:3]:
                    entries.append(entry)
            except:
                pass

        if not entries:
            await context.bot.send_message(chat_id, f"❌ No {category} news available right now.", parse_mode=ParseMode.HTML)
            return

        lines = [
            f"{config['emoji']} <b>{config['label']} — LIVE FEED</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━", ""
        ]

        for entry in entries[:8]:
            lines.append(f"{config['color']} <a href='{entry.link}'>{entry.title}</a>")
            lines.append("")

        lines.extend(["━━━━━━━━━━━━━━━━━━━━━━━", "✝️ <i>The Final Trade — All glory to God</i>"])

        await context.bot.send_message(
            chat_id, "\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error loading {category} news.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# /LUNC & /USTC DEDICATED COMMANDS
# ============================================================
async def lunc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_full_signal(update.message.chat.id, "terra-luna", context)

async def ustc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_full_signal(update.message.chat.id, "terrausd", context)


# ============================================================
# /DASHBOARD COMMAND
# ============================================================
async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_dashboard(update.message.chat.id, context)

async def _send_dashboard(chat_id, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖥️ Open Terminal", url="https://finaltrade-dashboard-91me6lozz-irayecrypto-1565s-projects.vercel.app")],
    ])
    msg = (
        "🖥️ <b>THE FINAL TRADE TERMINAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Access the full cyberpunk dashboard with:\n"
        "📊 Live Charts  📈 Market Data  📰 News Feeds\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✝️ <i>The Final Trade — All glory to God</i>"
    )
    await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ============================================================
# /FORECAST — BTC & ETH + Fear & Greed
# ============================================================
async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = "bitcoin,ethereum"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        btc_price = data.get("bitcoin", {}).get("usd", 0)
        btc_change = data.get("bitcoin", {}).get("usd_24h_change", 0) or 0
        eth_price = data.get("ethereum", {}).get("usd", 0)
        eth_change = data.get("ethereum", {}).get("usd_24h_change", 0) or 0

        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            fg_text = f"😱 Fear & Greed: <b>{fg['value']}</b> ({fg['value_classification']})"
        except:
            fg_text = "Fear & Greed: unavailable"

        btc_arrow = "🟢▲" if btc_change > 0 else "🔴▼"
        eth_arrow = "🟢▲" if eth_change > 0 else "🔴▼"

        msg = (
            f"📉 <b>BTC & ETH FORECAST</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟠 <b>BTC:</b> ${btc_price:,.2f}  {btc_arrow} {btc_change:+.1f}%\n"
            f"🔷 <b>ETH:</b> ${eth_price:,.2f}  {eth_arrow} {eth_change:+.1f}%\n\n"
            f"{fg_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — All glory to God</i>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error loading forecast.\n<i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)
