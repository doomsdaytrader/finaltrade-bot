import logging
import threading
import asyncio
import time
import requests
import feedparser
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.constants import ParseMode
from config import BOT_TOKEN, GROUP_ID, TOPIC_NEWS, TOPIC_SURVIVAL, TOPIC_SIGNALS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from telegram_commands import (
    start_command, price_command, news_command,
    survival_command, dashboard_command,
    lunc_command, ustc_command, markets_command
)

# ============================================================
# HEALTH CHECK SERVER (keeps Render free tier alive)
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
# AUTO-POSTING ENGINE
# ============================================================
posted_news_urls = set()
posted_survival_urls = set()

def auto_post_loop(bot_token: str):
    """Background loop that auto-posts news and price alerts."""
    bot = Bot(token=bot_token)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            # Only auto-post if GROUP_ID is configured
            if GROUP_ID and GROUP_ID != "":
                # Auto-post crypto news
                loop.run_until_complete(auto_post_crypto_news(bot))
                time.sleep(5)

                # Auto-post survival/geopolitics news
                loop.run_until_complete(auto_post_survival_news(bot))
                time.sleep(5)

                # Auto-post price alert for significant movers
                loop.run_until_complete(auto_post_price_alert(bot))

        except Exception as e:
            logger.error(f"Auto-post error: {e}")

        # Wait 5 minutes before next cycle
        time.sleep(300)


async def auto_post_crypto_news(bot: Bot):
    """Fetch and post latest crypto news to the group."""
    global posted_news_urls
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        for entry in feed.entries[:3]:
            if entry.link not in posted_news_urls:
                posted_news_urls.add(entry.link)

                msg = (
                    f"📰 <b>CRYPTO NEWS ALERT</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🔹 <b>{entry.title}</b>\n\n"
                    f"🔗 <a href='{entry.link}'>Read Full Article</a>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ <i>The Final Trade — All glory to God</i>"
                )

                topic_id = int(TOPIC_NEWS) if TOPIC_NEWS and TOPIC_NEWS != "0" else None

                await bot.send_message(
                    chat_id=int(GROUP_ID),
                    text=msg,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                    message_thread_id=topic_id
                )
                # Stagger posts
                await asyncio.sleep(2)

        # Keep set from growing too large
        if len(posted_news_urls) > 100:
            posted_news_urls = set(list(posted_news_urls)[-50:])

    except Exception as e:
        logger.error(f"Crypto news auto-post error: {e}")


async def auto_post_survival_news(bot: Bot):
    """Fetch and post geopolitics/survival news."""
    global posted_survival_urls
    try:
        feeds = [
            "https://www.reuters.com/world/rss",
        ]
        for rss_url in feeds:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:2]:
                if entry.link not in posted_survival_urls:
                    posted_survival_urls.add(entry.link)

                    msg = (
                        f"🌍 <b>GEOPOLITICS & SURVIVAL ALERT</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🔸 <b>{entry.title}</b>\n\n"
                        f"🔗 <a href='{entry.link}'>Full Report</a>\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚡ <i>The Final Trade — All glory to God</i>"
                    )

                    topic_id = int(TOPIC_SURVIVAL) if TOPIC_SURVIVAL and TOPIC_SURVIVAL != "0" else None

                    await bot.send_message(
                        chat_id=int(GROUP_ID),
                        text=msg,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False,
                        message_thread_id=topic_id
                    )
                    await asyncio.sleep(2)

        if len(posted_survival_urls) > 100:
            posted_survival_urls = set(list(posted_survival_urls)[-50:])

    except Exception as e:
        logger.error(f"Survival news auto-post error: {e}")


async def auto_post_price_alert(bot: Bot):
    """Post price overview for major coins."""
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

        lines = [
            "📊 <b>MARKET PULSE — AUTO UPDATE</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            ""
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
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "⚡ <i>The Final Trade — All glory to God</i>"
        ])

        topic_id = int(TOPIC_SIGNALS) if TOPIC_SIGNALS and TOPIC_SIGNALS != "0" else None

        await bot.send_message(
            chat_id=int(GROUP_ID),
            text="\n".join(lines),
            parse_mode=ParseMode.HTML,
            message_thread_id=topic_id
        )

    except Exception as e:
        logger.error(f"Price alert auto-post error: {e}")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Please configure BOT_TOKEN environment variable.")
        exit(1)

    # Start health check server
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print("Health server running on port 10000")

    # Start auto-posting engine (only if GROUP_ID is set)
    if GROUP_ID and GROUP_ID != "":
        auto_thread = threading.Thread(target=auto_post_loop, args=(BOT_TOKEN,), daemon=True)
        auto_thread.start()
        print(f"Auto-posting engine started for group {GROUP_ID}")
    else:
        print("No GROUP_ID set — auto-posting disabled. Set GROUP_ID env var to enable.")

    # Build and start the bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("markets", markets_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("survival", survival_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CommandHandler("lunc", lunc_command))
    app.add_handler(CommandHandler("ustc", ustc_command))

    print("Bot is up and running. All glory to God!")
    app.run_polling()
