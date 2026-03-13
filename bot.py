import logging
import threading
import asyncio
import time
import requests
import feedparser
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from config import (
    BOT_TOKEN, GROUP_ID, WEEX_REF,
    TOPIC_NEWS, TOPIC_SURVIVAL, TOPIC_SIGNALS,
    NEWS_FEEDS, CATEGORY_CONFIG, COINGECKO_COIN, FEAR_GREED_API
)
from telegram_commands import (
    start_command, price_command, token_command,
    news_command, survival_command, science_command,
    dashboard_command, lunc_command, ustc_command,
    markets_command, forecast_command, button_callback,
    estimate_rsi, generate_ai_signal, fetch_coin_detail
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================================
# HEALTH CHECK SERVER
# ============================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"alive","bot":"TheFinalTradeBot","glory":"to God"}')
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
    server.serve_forever()


# ============================================================
# AUTO-POSTING ENGINE (runs in background thread)
# ============================================================
posted_urls = set()

def auto_post_loop(bot_token: str):
    """Background loop: auto-posts news and price alerts to the group."""
    bot = Bot(token=bot_token)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Initial delay to let bot fully start
    time.sleep(10)
    logger.info("Auto-posting engine started!")

    while True:
        try:
            if GROUP_ID and GROUP_ID != "":
                # Post news from ALL categories
                for category, feeds in NEWS_FEEDS.items():
                    loop.run_until_complete(
                        auto_post_category(bot, category, feeds)
                    )
                    time.sleep(3)

                # Post market pulse
                loop.run_until_complete(auto_post_market_pulse(bot))

        except Exception as e:
            logger.error(f"Auto-post cycle error: {e}")

        # Wait 10 minutes between cycles
        time.sleep(600)


async def auto_post_category(bot: Bot, category: str, feeds: list):
    """Fetch RSS feeds for a category and auto-post new entries."""
    global posted_urls
    config = CATEGORY_CONFIG.get(category, {"emoji": "📰", "label": category.upper(), "color": "⚪"})

    # Determine which topic to post to
    topic_map = {
        "crypto": TOPIC_NEWS,
        "world": TOPIC_SURVIVAL,
        "survival": TOPIC_SURVIVAL,
        "science": TOPIC_NEWS,
    }
    topic_id_str = topic_map.get(category, "0")
    topic_id = int(topic_id_str) if topic_id_str and topic_id_str != "0" else None

    for rss_url in feeds:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:2]:
                if entry.link not in posted_urls:
                    posted_urls.add(entry.link)

                    msg = (
                        f"{config['emoji']} <b>{config['label']} ALERT</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"{config['color']} <b>{entry.title}</b>\n\n"
                        f"🔗 <a href='{entry.link}'>Read Full Report</a>\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"✝️ <i>The Final Trade — All glory to God</i>\n"
                        f"#TheFinalTrade #{category}"
                    )

                    await bot.send_message(
                        chat_id=int(GROUP_ID),
                        text=msg,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False,
                        message_thread_id=topic_id
                    )
                    await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"Auto-post {category} error for {rss_url}: {e}")

    # Prevent memory leak from growing set
    if len(posted_urls) > 200:
        posted_urls = set(list(posted_urls)[-100:])


async def auto_post_market_pulse(bot: Bot):
    """Auto-post a market overview with AI signals to the group."""
    try:
        coins = "bitcoin,ethereum,solana,binancecoin,terra-luna,terrausd"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        display = [
            ("bitcoin", "BTC", "🟠"), ("ethereum", "ETH", "🔷"),
            ("solana", "SOL", "🟣"), ("binancecoin", "BNB", "🟡"),
            ("terra-luna", "LUNC", "🔵"), ("terrausd", "USTC", "🟢"),
        ]

        # Fear & Greed
        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            fg_text = f"😱 Fear & Greed: <b>{fg['value']}</b> ({fg['value_classification']})\n"
        except:
            pass

        lines = [
            "📊 <b>MARKET PULSE — AUTO SIGNAL</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            fg_text
        ]

        for cg_id, symbol, emoji in display:
            if cg_id in data:
                price = data[cg_id]["usd"]
                change = data[cg_id].get("usd_24h_change", 0) or 0
                arrow = "🟢▲" if change > 0 else "🔴▼" if change < 0 else "⚪▬"
                p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
                lines.append(f"{emoji} <b>{symbol}</b>  {p_str}  {arrow} {change:+.1f}%")

        lines.extend([
            "",
            f"📈 <a href='https://www.weex.com/en?vipCode={WEEX_REF}'>Trade Now on WEEX</a>",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "✝️ <i>The Final Trade — All glory to God</i>",
            "#TheFinalTrade #MarketPulse #crypto"
        ])

        topic_id = int(TOPIC_SIGNALS) if TOPIC_SIGNALS and TOPIC_SIGNALS != "0" else None

        await bot.send_message(
            chat_id=int(GROUP_ID),
            text="\n".join(lines),
            parse_mode=ParseMode.HTML,
            message_thread_id=topic_id
        )
    except Exception as e:
        logger.error(f"Market pulse auto-post error: {e}")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set.")
        exit(1)

    # Health server
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server on port 10000")

    # Auto-posting engine
    if GROUP_ID:
        threading.Thread(target=auto_post_loop, args=(BOT_TOKEN,), daemon=True).start()
        print(f"Auto-posting engine armed for group {GROUP_ID}")
    else:
        print("No GROUP_ID — auto-posting disabled. Set GROUP_ID env var to enable.")

    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("token", token_command))
    app.add_handler(CommandHandler("markets", markets_command))
    app.add_handler(CommandHandler("forecast", forecast_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("survival", survival_command))
    app.add_handler(CommandHandler("science", science_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CommandHandler("lunc", lunc_command))
    app.add_handler(CommandHandler("ustc", ustc_command))

    # Inline button callback handler
    app.add_handler(CallbackQueryHandler(button_callback))

    print("✝️ The Final Trade Bot — All glory to God! Bot is LIVE.")
    app.run_polling()
