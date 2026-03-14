import re
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
# THUMBNAIL EXTRACTOR — Pulls images from RSS entries
# ============================================================
def extract_thumbnail(entry):
    """Extract the best available thumbnail from an RSS feed entry."""
    # 1. Check media_thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')

    # 2. Check media_content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            url = media.get('url', '')
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                return url
        # Return first media_content even if not image extension
        return entry.media_content[0].get('url', '')

    # 3. Check enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href', '') or enc.get('url', '')

    # 4. Check for image links
    if hasattr(entry, 'links'):
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href', '')

    # 5. Scrape from summary/content HTML
    content = ''
    if hasattr(entry, 'summary'):
        content = entry.summary
    elif hasattr(entry, 'content') and entry.content:
        content = entry.content[0].get('value', '')

    if content:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        if img_match:
            return img_match.group(1)

    return None


def extract_summary(entry, max_len=200):
    """Extract a clean text summary from RSS entry."""
    summary = ''
    if hasattr(entry, 'summary') and entry.summary:
        summary = entry.summary
    elif hasattr(entry, 'description') and entry.description:
        summary = entry.description
    elif hasattr(entry, 'content') and entry.content:
        summary = entry.content[0].get('value', '')

    # Strip HTML tags
    clean = re.sub(r'<[^>]+>', '', summary).strip()
    # Truncate
    if len(clean) > max_len:
        clean = clean[:max_len].rsplit(' ', 1)[0] + '...'
    return clean


# ============================================================
# RSI ESTIMATION
# ============================================================
def estimate_rsi(prices):
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
    price = data['market_data']['current_price']['usd']
    change = data['market_data'].get('price_change_percentage_24h', 0) or 0
    sparkline = data['market_data'].get('sparkline_7d', {}).get('price', [])
    rsi = estimate_rsi(sparkline[-24:]) if len(sparkline) >= 14 else 50.0

    if rsi > 70:
        mood = "🔴 OVERBOUGHT — Pullback zone"
        action = "⚠️ Take profits / tighten stops"
        bar = "🔴🔴🔴🔴🔴🔴🔴⚪⚪⚪"
    elif rsi > 55:
        mood = "🟡 BULLISH — Momentum building"
        action = "📈 Trail stops, ride the wave"
        bar = "🟡🟡🟡🟡🟡🟡⚪⚪⚪⚪"
    elif rsi > 45:
        mood = "⚪ NEUTRAL — Consolidation"
        action = "⏳ Wait for breakout confirmation"
        bar = "⚪⚪⚪⚪⚪⚪⚪⚪⚪⚪"
    elif rsi > 30:
        mood = "🟢 DIPPING — Accumulation zone"
        action = "💰 Dollar-cost average in"
        bar = "🟢🟢🟢🟢⚪⚪⚪⚪⚪⚪"
    else:
        mood = "💎 OVERSOLD — Whale entry zone"
        action = "🐋 Strong buy signal for holders"
        bar = "💎💎💎💎💎💎💎💎⚪⚪"

    trend = "✅ Bullish continuation" if change > 0 else "⚠️ Bearish pressure"
    vol_label = "📊 High volatility — scalp opportunities" if abs(change) > 5 else "📊 Low volatility — ranging"

    signal = (
        f"🧠 <b>AI SIGNAL ANALYSIS</b>\n"
        f"┣ RSI: <b>{rsi}</b> — {mood}\n"
        f"┣ {bar}\n"
        f"┣ Trend: {trend} ({change:+.2f}%)\n"
        f"┣ {vol_label}\n"
        f"┣ Action: {action}\n"
        f"┗ ⚡ Leverage: 10x-20x short bursts"
    )
    return signal, rsi


# ============================================================
# FETCH COIN DETAIL
# ============================================================
def fetch_coin_detail(coin_id: str):
    url = COINGECKO_COIN.format(coin_id)
    params = "?localization=false&tickers=false&community_data=false&developer_data=false&sparkline=true"
    r = requests.get(url + params, timeout=15)
    return r.json()


# ============================================================
# /START — Interactive Menu
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
            InlineKeyboardButton("📊 Markets", callback_data="cmd_markets"),
            InlineKeyboardButton("😱 Fear & Greed", callback_data="cmd_feargreed"),
        ],
        [
            InlineKeyboardButton("📰 Crypto News", callback_data="cmd_crypto"),
            InlineKeyboardButton("💹 Finance", callback_data="cmd_finance"),
        ],
        [
            InlineKeyboardButton("🌍 World News", callback_data="cmd_world"),
            InlineKeyboardButton("⚔️ War & Conflict", callback_data="cmd_conflict"),
        ],
        [
            InlineKeyboardButton("🛡️ Survival", callback_data="cmd_survival"),
            InlineKeyboardButton("🏥 Health", callback_data="cmd_health"),
        ],
        [
            InlineKeyboardButton("🔬 NASA & Space", callback_data="cmd_science"),
            InlineKeyboardButton("⛽ Energy Crisis", callback_data="cmd_energy"),
        ],
        [
            InlineKeyboardButton("🔍 Token Scanner", callback_data="cmd_scanner"),
            InlineKeyboardButton("🖥️ Terminal", callback_data="cmd_dashboard"),
        ],
        [InlineKeyboardButton("⚠️ Disclaimer", callback_data="cmd_disclaimer")],
    ])

    msg = (
        "✝️ <b>WELCOME TO THE FINAL TRADE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🙏 <i>All glory goes to God.</i>\n\n"
        "🧠 <b>AI-Powered Intelligence Hub:</b>\n\n"
        "📊 Crypto — AI Signals, RSI, Leverage\n"
        "💹 Finance — Markets, Fear & Greed\n"
        "🌍 World — BBC, NYT, Reuters, Al Jazeera\n"
        "⚔️ Conflict — War zones, defense intel\n"
        "🛡️ Survival — NOAA, USGS, WHO, FEMA\n"
        "🏥 Health — WHO, pandemic tracking\n"
        "🔬 Science — NASA, Space.com\n"
        "⛽ Energy — Oil, resource crisis\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>30+ live feeds. 24/7 auto-alerts.</b>\n"
        "Tap any button below to begin."
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ============================================================
# CALLBACK HANDLER
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
    elif data.startswith("cmd_") and data.replace("cmd_", "") in NEWS_FEEDS:
        category = data.replace("cmd_", "")
        await _send_rss_news(query.message.chat.id, category, context)
    elif data == "cmd_scanner":
        await context.bot.send_message(
            query.message.chat.id,
            "🔍 <b>Token Scanner</b>\n\nScan any coin with:\n<code>/token sol</code>\n<code>/token doge</code>\n<code>/token xrp</code>\n<code>/token avax</code>",
            parse_mode=ParseMode.HTML
        )
    elif data == "cmd_dashboard":
        await _send_dashboard(query.message.chat.id, context)
    elif data == "cmd_disclaimer":
        await context.bot.send_message(
            query.message.chat.id,
            "⚠️ <b>Disclaimer</b>\n\nFor educational and informational purposes only. "
            "Not financial advice. Trade at your own risk.\n\n✝️ <i>All glory to God.</i>",
            parse_mode=ParseMode.HTML
        )
    elif data == "cmd_back":
        await context.bot.send_message(
            query.message.chat.id,
            "Type /start to return to the main menu.",
            parse_mode=ParseMode.HTML
        )


# ============================================================
# FULL SIGNAL — Logo + RSI + AI + Market Data + WEEX
# ============================================================
async def _send_full_signal(chat_id, coin_id, context):
    try:
        data = fetch_coin_detail(coin_id)
        name = data.get('name', coin_id.upper())
        symbol = data.get('symbol', '').upper()
        price = data['market_data']['current_price']['usd']
        change_1h = data['market_data'].get('price_change_percentage_1h_in_currency', {}).get('usd', 0) or 0
        change_24h = data['market_data'].get('price_change_percentage_24h', 0) or 0
        change_7d = data['market_data'].get('price_change_percentage_7d', 0) or 0
        change_30d = data['market_data'].get('price_change_percentage_30d', 0) or 0
        market_cap = data['market_data'].get('market_cap', {}).get('usd', 0) or 0
        volume = data['market_data'].get('total_volume', {}).get('usd', 0) or 0
        circulating = data['market_data'].get('circulating_supply', 0) or 0
        ath = data['market_data'].get('ath', {}).get('usd', 0) or 0
        ath_change = data['market_data'].get('ath_change_percentage', {}).get('usd', 0) or 0
        image_url = data.get('image', {}).get('large', '')

        ai_signal, rsi = generate_ai_signal(data)

        p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.8f}"
        mc_str = f"${market_cap/1e9:,.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:,.1f}M"
        vol_str = f"${volume/1e9:,.2f}B" if volume >= 1e9 else f"${volume/1e6:,.1f}M"
        ath_str = f"${ath:,.2f}" if ath >= 1 else f"${ath:,.6f}"
        circ_str = f"{circulating/1e9:,.2f}B" if circulating >= 1e9 else f"{circulating/1e6:,.1f}M"

        def arrow(v): return "🟢▲" if v > 0 else "🔴▼" if v < 0 else "⚪▬"

        weex_link = f"https://www.weex.com/en/spot/{symbol}_USDT?vipCode={WEEX_REF}"

        caption = (
            f"🚨 <b>{name} ({symbol}) — FULL SIGNAL</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> {p_str}\n"
            f"{arrow(change_1h)} <b>1h:</b> {change_1h:+.2f}%\n"
            f"{arrow(change_24h)} <b>24h:</b> {change_24h:+.2f}%\n"
            f"{arrow(change_7d)} <b>7d:</b> {change_7d:+.2f}%\n"
            f"{arrow(change_30d)} <b>30d:</b> {change_30d:+.2f}%\n\n"
            f"📊 <b>Market Cap:</b> {mc_str}\n"
            f"📈 <b>24h Volume:</b> {vol_str}\n"
            f"🔄 <b>Circulating:</b> {circ_str} {symbol}\n"
            f"🏆 <b>ATH:</b> {ath_str} ({ath_change:+.1f}% from ATH)\n\n"
            f"{ai_signal}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — All glory to God</i>"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📈 Trade {symbol} on WEEX", url=weex_link)],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="cmd_back")],
        ])

        if image_url:
            await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        else:
            await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: <i>{str(e)[:200]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# /PRICE & /TOKEN COMMANDS
# ============================================================
ALIASES = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "bnb": "binancecoin",
    "lunc": "terra-luna", "ustc": "terrausd", "xrp": "ripple", "doge": "dogecoin",
    "ada": "cardano", "dot": "polkadot", "avax": "avalanche-2", "matic": "matic-network",
    "shib": "shiba-inu", "link": "chainlink", "uni": "uniswap", "atom": "cosmos",
    "near": "near", "ftm": "fantom", "algo": "algorand", "sand": "the-sandbox",
}

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = (
            "📊 <b>Usage:</b> <code>/price bitcoin</code>\n\n"
            "🟠 BTC  🔷 ETH  🟣 SOL  🟡 BNB\n"
            "🔵 LUNC  🟢 USTC  ⚪ XRP  🟤 DOGE\n"
            "♦ ADA  🔗 LINK  🟣 DOT  ❄️ AVAX\n\n"
            "<i>Or use /token for full AI signal analysis</i>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return
    coin_id = ALIASES.get(context.args[0].lower(), context.args[0].lower())
    await _send_full_signal(update.message.chat.id, coin_id, context)

async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔍 <b>Token Scanner</b>\n\nUsage: <code>/token sol</code>", parse_mode=ParseMode.HTML)
        return
    coin_id = ALIASES.get(context.args[0].lower(), context.args[0].lower())
    await _send_full_signal(update.message.chat.id, coin_id, context)

async def hot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually triggers the Hottest Token scanner and dumps a new Setup."""
    from token_alerts import auto_post_hottest_tokens
    
    msg = await update.message.reply_text("📡 <i>Scanning highest volume breakout targets...</i>", parse_mode=ParseMode.HTML)
    try:
        # Override bot so it posts back to the same chat if we are testing outside supergroup
        await auto_post_hottest_tokens(context.bot)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


# ============================================================
# /MARKETS — Full overview + Fear & Greed
# ============================================================
async def markets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_markets(update.message.chat.id, context)

async def _send_markets(chat_id, context):
    coins = "bitcoin,ethereum,solana,binancecoin,terra-luna,terrausd,ripple,dogecoin,cardano,polkadot"
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        data = requests.get(url, timeout=10).json()

        display = [
            ("bitcoin","BTC","🟠"), ("ethereum","ETH","🔷"), ("solana","SOL","🟣"),
            ("binancecoin","BNB","🟡"), ("terra-luna","LUNC","🔵"), ("terrausd","USTC","🟢"),
            ("ripple","XRP","⚪"), ("dogecoin","DOGE","🟤"), ("cardano","ADA","♦"),
            ("polkadot","DOT","🟣"),
        ]

        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            val = int(fg['value'])
            fg_emoji = "😱" if val < 25 else "😰" if val < 50 else "😐" if val < 75 else "🤑"
            fg_bar = "🔴" * (val // 10) + "⚪" * (10 - val // 10)
            fg_text = f"{fg_emoji} <b>Fear & Greed:</b> {val}/100 ({fg['value_classification']})\n{fg_bar}\n"
        except:
            pass

        lines = [
            "🌐 <b>MARKET COMMAND CENTER</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            fg_text
        ]

        for cg_id, symbol, emoji in display:
            if cg_id in data:
                price = data[cg_id]["usd"]
                change = data[cg_id].get("usd_24h_change", 0) or 0
                mc = data[cg_id].get("usd_market_cap", 0) or 0
                arrow = "🟢▲" if change > 0 else "🔴▼" if change < 0 else "⚪▬"
                p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
                mc_s = f"${mc/1e9:,.1f}B" if mc >= 1e9 else f"${mc/1e6:,.0f}M" if mc > 0 else ""
                mc_part = f"  [{mc_s}]" if mc_s else ""
                lines.append(f"{emoji} <b>{symbol}</b>  {p_str}  {arrow}{change:+.1f}%{mc_part}")

        lines.extend([
            "",
            f"📈 <a href='https://www.weex.com/en?vipCode={WEEX_REF}'>Trade Now on WEEX</a>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "✝️ <i>The Final Trade — All glory to God</i>"
        ])
        await context.bot.send_message(chat_id, "\n".join(lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error: <i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# FEAR & GREED
# ============================================================
async def _send_fear_greed(chat_id, context):
    try:
        fg = requests.get(FEAR_GREED_API, timeout=10).json()['data'][0]
        val = int(fg['value'])
        classification = fg['value_classification']

        if val < 20:   bar, emoji, insight = "🔴🔴🔴🔴🔴🔴🔴🔴⚪⚪", "😱", "EXTREME FEAR — Blood in the streets. Historically the best buy zone."
        elif val < 40: bar, emoji, insight = "🟠🟠🟠🟠🟠🟠⚪⚪⚪⚪", "😰", "FEAR — Smart money accumulating. Watch whale wallets."
        elif val < 60: bar, emoji, insight = "🟡🟡🟡🟡🟡🟡🟡⚪⚪⚪", "😐", "NEUTRAL — Market deciding direction. Stay alert."
        elif val < 80: bar, emoji, insight = "🟢🟢🟢🟢🟢🟢🟢🟢⚪⚪", "😊", "GREED — Confidence rising. Trail your stops."
        else:          bar, emoji, insight = "💰💰💰💰💰💰💰💰💰💰", "🤑", "EXTREME GREED — Euphoria! Tops form here. Protect capital."

        msg = (
            f"{emoji} <b>FEAR & GREED INDEX</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 <b>Score:</b> {val}/100\n"
            f"📈 <b>Status:</b> {classification}\n"
            f"{bar}\n\n"
            f"💡 <b>Insight:</b> {insight}\n\n"
            f"🧠 <b>What this means:</b>\n"
            f"┣ Below 25 = Historic buying opportunities\n"
            f"┣ 25-50 = Accumulation phase\n"
            f"┣ 50-75 = Bull market building\n"
            f"┗ Above 75 = Distribution / exit zones\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — All glory to God</i>"
        )
        await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error: <i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# RSS NEWS COMMANDS — With thumbnails
# All categories share the same rich format
# ============================================================
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "crypto", context)

async def survival_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "survival", context)

async def science_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "science", context)

async def conflict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "conflict", context)

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "health", context)

async def energy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "energy", context)

async def finance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_rss_news(update.message.chat.id, "finance", context)

async def _send_rss_news(chat_id, category, context):
    """Send news articles with thumbnails where available."""
    try:
        config = CATEGORY_CONFIG.get(category, {"emoji": "📰", "label": category.upper(), "color": "⚪", "hashtag": ""})
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
            await context.bot.send_message(chat_id, f"❌ No {category} news available right now.")
            return

        # Send first article with thumbnail as photo
        sent_photo = False
        for entry in entries[:1]:
            thumb = extract_thumbnail(entry)
            summary = extract_summary(entry, 250)
            caption = (
                f"{config['emoji']} <b>{config['label']}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📌 <b>{entry.title}</b>\n\n"
                f"{summary}\n\n"
                f"🔗 <a href='{entry.link}'>Read Full Article</a>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✝️ <i>The Final Trade</i> {config['hashtag']}"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Open Article", url=entry.link)],
            ])

            if thumb:
                try:
                    await context.bot.send_photo(chat_id=chat_id, photo=thumb, caption=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard)
                    sent_photo = True
                except:
                    await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=False)
            else:
                await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=False)

        # Send remaining articles as a consolidated text list
        if len(entries) > 1:
            remaining_lines = [f"{config['emoji']} <b>MORE {config['label']} HEADLINES</b>", "━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
            for entry in entries[1:8]:
                remaining_lines.append(f"{config['color']} <a href='{entry.link}'>{entry.title}</a>")
                remaining_lines.append("")
            remaining_lines.extend(["━━━━━━━━━━━━━━━━━━━━━━━━━━", f"✝️ <i>The Final Trade</i> {config['hashtag']}"])
            await context.bot.send_message(chat_id, "\n".join(remaining_lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Error: <i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)


# ============================================================
# /LUNC, /USTC, /DASHBOARD, /FORECAST
# ============================================================
async def lunc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_full_signal(update.message.chat.id, "terra-luna", context)

async def ustc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_full_signal(update.message.chat.id, "terrausd", context)

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_dashboard(update.message.chat.id, context)

async def _send_dashboard(chat_id, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖥️ Open Terminal", url="https://finaltrade-dashboard-91me6lozz-irayecrypto-1565s-projects.vercel.app")],
    ])
    msg = (
        "🖥️ <b>THE FINAL TRADE TERMINAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 Live Charts  📈 Market Data  📰 News\n"
        "🧠 AI Signals  🛡️ Survival Intel\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✝️ <i>The Final Trade — All glory to God</i>"
    )
    await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = "bitcoin,ethereum"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()
        btc_p = data.get("bitcoin",{}).get("usd",0)
        btc_c = data.get("bitcoin",{}).get("usd_24h_change",0) or 0
        eth_p = data.get("ethereum",{}).get("usd",0)
        eth_c = data.get("ethereum",{}).get("usd_24h_change",0) or 0

        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            fg_text = f"😱 <b>Fear & Greed:</b> {fg['value']} ({fg['value_classification']})\n"
        except:
            pass

        ba = "🟢▲" if btc_c > 0 else "🔴▼"
        ea = "🟢▲" if eth_c > 0 else "🔴▼"

        msg = (
            f"📉 <b>BTC & ETH FORECAST</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟠 <b>BTC:</b> ${btc_p:,.2f}  {ba} {btc_c:+.1f}%\n"
            f"🔷 <b>ETH:</b> ${eth_p:,.2f}  {ea} {eth_c:+.1f}%\n\n"
            f"{fg_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — All glory to God</i>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: <i>{str(e)[:100]}</i>", parse_mode=ParseMode.HTML)
