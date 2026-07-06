# -*- coding: utf-8 -*-
import logging
import threading
import asyncio
import time
import requests
import feedparser
import re
import random
import html as html_module
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from config import (
    BOT_TOKEN, GROUP_ID, WEEX_REF, BYDFI_REF, BITUNIX_REF, BYBIT_REF, KCEX_REF,
    BITBASE_REF, VOOX_REF, BITMART_REF, ORANGEX_REF,
    TOPIC_NEWS, TOPIC_SURVIVAL, TOPIC_SIGNALS, TOPIC_MARKET,
    NEWS_FEEDS, CATEGORY_CONFIG, FEAR_GREED_API
)
from telegram_commands import (
    start_command, price_command, token_command, hot_command,
    news_command, survival_command, science_command,
    conflict_command, health_command, energy_command, finance_command,
    dashboard_command, lunc_command, ustc_command,
    markets_command, forecast_command, button_callback,
    extract_thumbnail, extract_summary
)
from token_alerts import auto_post_hottest_tokens
from survival_hacks import auto_post_survival_hack

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

posted_urls = set()
try:
    if os.path.exists("posted_urls.txt"):
        with open("posted_urls.txt", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    posted_urls.add(line.strip())
except Exception:
    pass

recent_news_digest = []
last_digest_time = time.time()


# ============================================================
# HEALTH SERVER
# ============================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/logs':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            try:
                with open("bot.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    self.wfile.write("".join(lines[-100:]).encode("utf-8"))
            except Exception as e:
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"alive","bot":"AyewakenFuturesBot"}')

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
    server.serve_forever()


# ============================================================
# URGENT KEYWORD DETECTION
# ============================================================
URGENT_KEYWORDS = [
    'breaking', 'urgent', 'emergency', 'crash', 'collapse', 'surge', 'plunge',
    'hack', 'exploit', 'ban', 'war', 'attack', 'explosion', 'earthquake',
    'shutdown', 'halt', 'seized', 'arrested', 'blackout', 'outbreak'
]

def is_urgent(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in URGENT_KEYWORDS)


# ============================================================
# AUTO-POST ENGINE V17 — Priority Queue + Soothing Cadence
# ============================================================
def auto_post_loop(bot_token: str):
    bot = Bot(token=bot_token)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    time.sleep(5)
    logger.info("=== AUTO-POST ENGINE V17 STARTED === PRIORITY QUEUE MODE ===")

    # --- Timers ---
    last_priority_time = 0      # LUNC, USTC, BTC, ETH — every 11 min
    last_general_time  = 0      # All other tokens     — every 30 min
    last_news_time     = 0      # News categories      — every 20-30 min
    global last_digest_time

    # --- Priority queue: rotates LUNC → BTC → USTC → ETH → repeat ---
    PRIORITY_SYMBOLS = ["lunc", "btc", "ustc", "eth"]
    priority_index = 0

    # --- General tokens (excluding priority ones) ---
    GENERAL_EXCLUDE = {"lunc", "btc", "ustc", "eth", "terra-luna", "terrausd",
                       "bitcoin", "ethereum"}

    # --- News categories ---
    categories   = list(NEWS_FEEDS.keys())
    cat_index    = 0
    hack_counter = 0

    # Stagger: priority fires first, then wait before general and news
    next_priority_wait = 0
    next_general_wait  = 30 * 60   # first general fires 30 min after start
    next_news_wait     = 5  * 60   # first news fires 5 min after start

    while True:
        try:
            current_time = time.time()

            # Keep Render alive
            try:
                requests.get("https://finaltrade-bot.onrender.com/", timeout=10)
                requests.get("https://finaltrade-api.onrender.com/health", timeout=10)
            except Exception:
                pass

            if GROUP_ID:

                # === ENGINE 1: PRIORITY SIGNALS — LUNC / BTC / USTC / ETH every 11 min ===
                if current_time - last_priority_time >= next_priority_wait:
                    sym = PRIORITY_SYMBOLS[priority_index % len(PRIORITY_SYMBOLS)]
                    logger.info(f">>> [PRIORITY] Firing {sym.upper()} signal...")
                    try:
                        loop.run_until_complete(
                            auto_post_hottest_tokens(bot, force_symbol=sym)
                        )
                        logger.info(f">>> [PRIORITY] {sym.upper()} SENT")
                        priority_index += 1
                    except Exception as e:
                        logger.error(f">>> [PRIORITY] FAILED: {e}")

                    last_priority_time = time.time()
                    current_time = time.time()
                    next_priority_wait = 11 * 60   # always exactly 11 min
                    logger.info(">>> [PRIORITY] Next in 11 min")

                # === ENGINE 2: GENERAL CRYPTO — all others every 30 min ===
                if current_time - last_general_time >= next_general_wait:
                    logger.info(">>> [GENERAL] Firing altcoin signal...")
                    try:
                        loop.run_until_complete(
                            auto_post_hottest_tokens(bot, exclude_symbols=GENERAL_EXCLUDE)
                        )
                        logger.info(">>> [GENERAL] ALTCOIN SIGNAL SENT")
                    except Exception as e:
                        logger.error(f">>> [GENERAL] FAILED: {e}")

                    last_general_time = time.time()
                    current_time = time.time()
                    next_general_wait = 30 * 60
                    logger.info(">>> [GENERAL] Next in 30 min")

                # === ENGINE 3: NEWS — one category every 20-30 min ===
                if current_time - last_news_time >= next_news_wait:
                    category = categories[cat_index]
                    feeds    = NEWS_FEEDS[category]
                    logger.info(f">>> [NEWS] Posting category: {category}")
                    try:
                        loop.run_until_complete(auto_post_category(bot, category, feeds))
                    except Exception as e:
                        logger.error(f">>> [NEWS] FAILED ({category}): {e}")

                    cat_index += 1

                    # Market Pulse every 3 categories
                    if cat_index % 3 == 0:
                        try:
                            loop.run_until_complete(auto_post_market_pulse(bot))
                            logger.info(">>> [NEWS] MARKET PULSE SENT")
                        except Exception as e:
                            logger.error(f">>> [NEWS] Market pulse failed: {e}")

                    # Full cycle complete → survival hack
                    if cat_index >= len(categories):
                        cat_index = 0
                        hack_counter += 1
                        if hack_counter >= 3:
                            try:
                                loop.run_until_complete(auto_post_survival_hack(bot))
                                logger.info(">>> [NEWS] SURVIVAL HACK SENT")
                            except Exception as e:
                                logger.error(f">>> [NEWS] Survival hack failed: {e}")
                            hack_counter = 0

                    last_news_time = time.time()
                    current_time   = time.time()
                    wait_mins      = random.randint(20, 30)
                    next_news_wait = wait_mins * 60
                    logger.info(f">>> [NEWS] Next in {wait_mins} min")

                # === 2-HOUR DIGEST ===
                if current_time - last_digest_time >= 7200:
                    try:
                        loop.run_until_complete(auto_post_2hr_digest(bot))
                        logger.info(">>> DIGEST SENT")
                    except Exception as e:
                        logger.error(f">>> DIGEST FAILED: {e}")
                    last_digest_time = time.time()

        except Exception as e:
            logger.error(f"Auto-post cycle error: {e}")

        # Tick every 30 seconds
        time.sleep(30)


                    current_time = time.time()

                # === 3. 2-HOUR DIGEST ===
                if current_time - last_digest_time >= 7200:
                    try:
                        loop.run_until_complete(auto_post_2hr_digest(bot))
                    except Exception as digest_err:
                        logger.error(f"Error posting digest: {digest_err}")
                    last_digest_time = time.time()

        except Exception as e:
            logger.error(f"Auto-post cycle error: {e}")

        # Tick frequency: check timers every 30 seconds
        time.sleep(30)


# ============================================================
# AUTO-POST: RSS CATEGORY (Urgent → Immediate | Others → Digest)
# ============================================================
async def auto_post_category(bot: Bot, category: str, feeds: list):
    """Post urgent articles immediately. Group non-urgent into a clean digest."""
    global posted_urls, recent_news_digest
    config = CATEGORY_CONFIG.get(category, {"emoji": "📰", "label": category.upper(), "color": "⚪", "hashtag": ""})

    topic_map = {
        "crypto": TOPIC_NEWS, "finance": TOPIC_NEWS,
        "world": TOPIC_SURVIVAL, "survival": TOPIC_SURVIVAL,
        "conflict": TOPIC_SURVIVAL, "energy": TOPIC_SURVIVAL,
        "science": TOPIC_NEWS, "health": TOPIC_SURVIVAL,
    }
    topic_id_str = topic_map.get(category, "0")
    topic_id = int(topic_id_str) if topic_id_str and topic_id_str != "0" else None

    urgent_articles = []
    digest_articles = []

    for rss_url in feeds:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]:
                if entry.link not in posted_urls:
                    posted_urls.add(entry.link)
                    try:
                        with open("posted_urls.txt", "a", encoding="utf-8") as f:
                            f.write(entry.link + "\n")
                    except Exception:
                        pass
                    
                    thumb = extract_thumbnail(entry)
                    summary = extract_summary(entry, 350)
                    safe_title = html_module.escape(entry.title)
                    recent_news_digest.append(f"{config['emoji']} <a href='{entry.link}'>{safe_title}</a>")
                    if len(recent_news_digest) > 40:
                        recent_news_digest.pop(0)
                    if is_urgent(entry.title):
                        urgent_articles.append((entry, thumb, summary, safe_title))
                    else:
                        digest_articles.append((entry, thumb, summary, safe_title))
        except Exception as e:
            logger.error(f"Feed parse error ({rss_url}): {e}")

    # --- Post urgent articles immediately, one per post ---
    for entry, thumb, summary, safe_title in urgent_articles:
        commodity_link = ""
        if any(kw in (entry.title + summary).lower() for kw in ['gold', 'silver', 'oil', 'platinum']):
            commodity_link = f"\n\n⛏️ <b>Trade Commodities on BYDFi:</b> <a href='https://partner.bydfi.com/register?vipCode={BYDFI_REF}'>Click Here</a>"
        caption = (
            f"🚨 <b>URGENT — {config['label']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>{safe_title}</b>\n\n"
            f"{summary}\n\n"
            f"🔗 <a href='{entry.link}'>Read Full Report</a>{commodity_link}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ <i>AYEWAKEN FUTURES</i> {config['hashtag']}"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Read Full Article", url=entry.link)]])
        sent = False
        if thumb:
            try:
                await bot.send_photo(chat_id=int(GROUP_ID), photo=thumb, caption=caption,
                    parse_mode=ParseMode.HTML, reply_markup=keyboard, message_thread_id=topic_id)
                sent = True
            except Exception as img_err:
                logger.warning(f"Urgent photo failed: {img_err}")
        if not sent:
            await bot.send_message(chat_id=int(GROUP_ID), text=caption,
                parse_mode=ParseMode.HTML, reply_markup=keyboard,
                disable_web_page_preview=False, message_thread_id=topic_id)
        await asyncio.sleep(5)

    # --- Post non-urgent as grouped digest ---
    if digest_articles:
        if len(digest_articles) == 1:
            entry, thumb, summary, safe_title = digest_articles[0]
            caption = (
                f"{config['emoji']} <b>{config['label']} UPDATE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📌 <b>{safe_title}</b>\n\n"
                f"{summary}\n\n"
                f"🔗 <a href='{entry.link}'>Read Full Report</a>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✍️ <i>AYEWAKEN FUTURES</i> {config['hashtag']}"
            )
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Read Article", url=entry.link)]])
            sent = False
            if thumb:
                try:
                    await bot.send_photo(chat_id=int(GROUP_ID), photo=thumb, caption=caption,
                        parse_mode=ParseMode.HTML, reply_markup=keyboard, message_thread_id=topic_id)
                    sent = True
                except Exception:
                    pass
            if not sent:
                await bot.send_message(chat_id=int(GROUP_ID), text=caption,
                    parse_mode=ParseMode.HTML, disable_web_page_preview=False, message_thread_id=topic_id)
        else:
            # Multiple articles — clean numbered digest post
            lines = [
                f"{config['emoji']} <b>{config['label']} — NEWS ROUNDUP</b>",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            ]
            buttons = []
            for i, (entry, thumb, summary, safe_title) in enumerate(digest_articles[:5], 1):
                short = summary[:200].rsplit(' ', 1)[0] + '...' if len(summary) > 200 else summary
                lines.append(f"<b>{i}. {safe_title}</b>")
                if short:
                    lines.append(f"<i>{short}</i>")
                lines.append(f"🔗 <a href='{entry.link}'>Read more</a>\n")
                buttons.append([InlineKeyboardButton(f"📰 Story {i}", url=entry.link)])
            lines.extend([
                "━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"✍️ <i>AYEWAKEN FUTURES</i> {config['hashtag']}"
            ])
            keyboard = InlineKeyboardMarkup(buttons[:5])
            await bot.send_message(chat_id=int(GROUP_ID), text="\n".join(lines),
                parse_mode=ParseMode.HTML, reply_markup=keyboard,
                disable_web_page_preview=True, message_thread_id=topic_id)

    if len(posted_urls) > 1000:
        keep = list(posted_urls)[-500:]
        posted_urls = set(keep)
        try:
            with open("posted_urls.txt", "w", encoding="utf-8") as f:
                for link in keep:
                    f.write(link + "\n")
        except Exception:
            pass


# ============================================================
# AUTO-POST: 2-HOUR GLOBAL DIGEST
# ============================================================
async def auto_post_2hr_digest(bot: Bot):
    """Posts a 2-hour roll-up digest of all recent alerts."""
    global recent_news_digest
    if not recent_news_digest:
        return
    try:
        lines = [
            "🌍 <b>AYEWAKEN FUTURES — 2-HOUR GLOBAL DIGEST</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        display_news = random.sample(recent_news_digest, min(len(recent_news_digest), 10))
        for item in display_news:
            lines.append(item)
            lines.append("")
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "✍️ <i>AYEWAKEN FUTURES — All glory to God.</i>"
        ])
        topic_id = int(TOPIC_NEWS) if TOPIC_NEWS and TOPIC_NEWS != "0" else None
        await bot.send_message(
            chat_id=int(GROUP_ID),
            text="\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            message_thread_id=topic_id
        )
        recent_news_digest.clear()
    except Exception as e:
        logger.error(f"2Hr Digest error: {e}")


# ============================================================
# AUTO-POST: MARKET PULSE
# ============================================================
async def auto_post_market_pulse(bot: Bot):
    """Market overview with Fear & Greed auto-posted to group."""
    try:
        coins = "bitcoin,ethereum,solana,binancecoin,terra-luna,terrausd"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        display = [
            ("bitcoin", "BTC", "🟠"),
            ("ethereum", "ETH", "🔷"),
            ("solana", "SOL", "🟣"),
            ("binancecoin", "BNB", "🟡"),
            ("terra-luna", "LUNC", "🔵"),
            ("terrausd", "USTC", "🟢"),
        ]

        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            val = int(fg['value'])
            fg_emoji = "😱" if val < 25 else "😰" if val < 50 else "😊" if val < 75 else "🤑"
            fg_text = f"{fg_emoji} <b>Fear &amp; Greed:</b> {val}/100 ({fg['value_classification']})\n"
        except Exception:
            pass

        lines = [
            "📊 <b>MARKET PULSE — AUTO SIGNAL</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            fg_text
        ]

        for cg_id, symbol, emoji in display:
            if cg_id in data:
                price = data[cg_id]["usd"]
                change = data[cg_id].get("usd_24h_change", 0) or 0
                arrow = "🟢▲" if change > 0 else "🔴▼" if change < 0 else "⚪▬"
                p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
                lines.append(f"{emoji} <b>{symbol}</b>  {p_str}  {arrow} {change:+.1f}%")

        exchanges = [
            ("Bybit", f"https://partner.bybit.com/b/{BYBIT_REF}"),
            ("WEEX", f"https://www.weex.com/en/register?vipCode={WEEX_REF}"),
            ("BYDFi", f"https://partner.bydfi.com/register?vipCode={BYDFI_REF}"),
            ("Bitunix", f"https://www.bitunix.com/register?vipCode={BITUNIX_REF}"),
            ("KCEX", f"https://www.kcex.com?inviteCode={KCEX_REF}")
        ]
        exchange_name, affiliate_link = random.choice(exchanges)

        lines.extend([
            "",
            f"📈 <a href='{affiliate_link}'>Trade on {exchange_name}</a>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "✍️ <i>AYEWAKEN FUTURES — All glory to God</i>",
            "#AyewakenFutures #MarketPulse #crypto"
        ])

        topic_id = int(TOPIC_MARKET) if TOPIC_MARKET and TOPIC_MARKET != "0" else None

        await bot.send_message(
            chat_id=int(GROUP_ID), text="\n".join(lines),
            parse_mode=ParseMode.HTML, message_thread_id=topic_id
        )
    except Exception as e:
        logger.error(f"Market pulse error: {e}")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set. Please set the BOT_TOKEN environment variable.")
        exit(1)

    # Start health server
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server running on port 10000")

    # Start auto-posting thread
    if GROUP_ID:
        threading.Thread(target=auto_post_loop, args=(BOT_TOKEN,), daemon=True).start()
        print(f"Auto-posting V16 armed for group {GROUP_ID}")
    else:
        print("No GROUP_ID set — auto-posting disabled.")

    # Build Telegram app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("token", token_command))
    app.add_handler(CommandHandler("hot", hot_command))
    app.add_handler(CommandHandler("markets", markets_command))
    app.add_handler(CommandHandler("forecast", forecast_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("survival", survival_command))
    app.add_handler(CommandHandler("science", science_command))
    app.add_handler(CommandHandler("conflict", conflict_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("energy", energy_command))
    app.add_handler(CommandHandler("finance", finance_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CommandHandler("lunc", lunc_command))
    app.add_handler(CommandHandler("ustc", ustc_command))

    app.add_handler(CallbackQueryHandler(button_callback))

    print("✅ AYEWAKEN FUTURES Bot V16 — All glory to God! LIVE.")
    app.run_polling()
