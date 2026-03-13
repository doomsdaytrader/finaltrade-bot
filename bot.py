import logging
import threading
import asyncio
import time
import requests
import feedparser
import re
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from config import (
    BOT_TOKEN, GROUP_ID, WEEX_REF,
    TOPIC_NEWS, TOPIC_SURVIVAL, TOPIC_SIGNALS,
    NEWS_FEEDS, CATEGORY_CONFIG, FEAR_GREED_API
)
from telegram_commands import (
    start_command, price_command, token_command,
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
    level=logging.INFO
)
logger = logging.getLogger(__name__)

posted_urls = set()
recent_news_digest = []
last_digest_time = time.time()



# ============================================================
# HEALTH SERVER
# ============================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"alive","bot":"TheFinalTradeBot","glory":"to God","version":"3.0"}')
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
    server.serve_forever()


# ============================================================
# AUTO-POST ENGINE — With thumbnails & rich formatting
# ============================================================

def auto_post_loop(bot_token: str):
    bot = Bot(token=bot_token)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    time.sleep(15)
    logger.info("Auto-posting engine V6 started! Continuous drip mode + 2hr digests.")

    pulse_counter = 0
    hack_counter = 0
    global last_digest_time

    while True:
        try:
            if GROUP_ID:
                # We want Crypto Signals to appear just as much as news.
                # So we will fire a token setup after every 2 news categories.
                cat_count = 0
                for category, feeds in NEWS_FEEDS.items():
                    loop.run_until_complete(auto_post_category(bot, category, feeds))
                    time.sleep(30)
                    
                    cat_count += 1
                    
                    # Every 2 news categories, fire a Crypto Trade Setup
                    if cat_count % 2 == 0:
                        loop.run_until_complete(auto_post_hottest_tokens(bot))
                        time.sleep(15)
                    
                    # Every 4 news categories, fire the broad Market Pulse
                    if cat_count % 4 == 0:
                        loop.run_until_complete(auto_post_market_pulse(bot))
                        time.sleep(15)

                # Survival hack auto-post once per full cycle of news
                hack_counter += 1
                if hack_counter >= 2:
                    loop.run_until_complete(auto_post_survival_hack(bot))
                    hack_counter = 0

                # 2-Hour News Digest Rollup
                current_time = time.time()
                if current_time - last_digest_time >= 7200:
                    loop.run_until_complete(auto_post_2hr_digest(bot))
                    last_digest_time = current_time

        except Exception as e:
            logger.error(f"Auto-post cycle error: {e}")

        # Extremely short 15 second wait before restarting the entire cycle.
        time.sleep(15)


async def auto_post_category(bot: Bot, category: str, feeds: list):
    """Auto-post RSS articles with thumbnails to the group."""
    global posted_urls, recent_news_digest
    config = CATEGORY_CONFIG.get(category, {"emoji": "📰", "label": category.upper(), "color": "⚪", "hashtag": ""})

    # Route to correct topic
    topic_map = {
        "crypto": TOPIC_NEWS, "finance": TOPIC_NEWS,
        "world": TOPIC_SURVIVAL, "survival": TOPIC_SURVIVAL,
        "conflict": TOPIC_SURVIVAL, "energy": TOPIC_SURVIVAL,
        "science": TOPIC_NEWS, "health": TOPIC_SURVIVAL,
    }
    topic_id_str = topic_map.get(category, "0")
    topic_id = int(topic_id_str) if topic_id_str and topic_id_str != "0" else None

    for rss_url in feeds:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:2]:
                if entry.link not in posted_urls:
                    posted_urls.add(entry.link)

                    thumb = extract_thumbnail(entry)
                    summary = extract_summary(entry, 200)

                    # Track for 2-hour digest roll-up
                    recent_news_digest.append(f"{config['emoji']} <a href='{entry.link}'>{entry.title}</a>")
                    if len(recent_news_digest) > 40:
                        recent_news_digest.pop(0)

                    # Detect commodities for affiliate link injection
                    text_to_check = (entry.title + " " + summary).lower()
                    commodity_link = ""
                    commodities = ['gold', 'silver', 'oil', 'platinum', 'palladium', 'precious metal', 'rare earth']
                    if any(kw in text_to_check for kw in commodities):
                        from config import BYDFI_REF
                        commodity_link = f"\n\n⛏️ <b>Trade Commodities on BYDFi:</b> <a href='https://partner.bydfi.com/register?vipCode={BYDFI_REF}&f=Thefinaltrade'>Click Here</a>"

                    caption = (
                        f"{config['emoji']} <b>{config['label']} ALERT</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"📌 <b>{entry.title}</b>\n\n"
                    )
                    if summary:
                        caption += f"{summary}\n\n"
                    caption += (
                        f"🔗 <a href='{entry.link}'>Read Full Report</a>{commodity_link}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"✝️ <i>The Final Trade</i> {config['hashtag']}"
                    )

                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🌐 Read Article", url=entry.link)],
                    ])

                    # Try sending with thumbnail photo
                    sent = False
                    if thumb:
                        try:
                            await bot.send_photo(
                                chat_id=int(GROUP_ID), photo=thumb,
                                caption=caption, parse_mode=ParseMode.HTML,
                                reply_markup=keyboard,
                                message_thread_id=topic_id
                            )
                            sent = True
                        except Exception as img_err:
                            logger.warning(f"Photo send failed for {thumb}: {img_err}")

                    if not sent:
                        await bot.send_message(
                            chat_id=int(GROUP_ID), text=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=keyboard,
                            disable_web_page_preview=False,
                            message_thread_id=topic_id
                        )

                    await asyncio.sleep(4)

        except Exception as e:
            logger.error(f"Auto-post {category} error ({rss_url}): {e}")

    # Keep a deep cache so we don't repost links
    if len(posted_urls) > 1000:
        posted_urls = set(list(posted_urls)[-500:])

async def auto_post_2hr_digest(bot: Bot):
    """Posts a 2-hour roll-up digest of alerts and events to prevent spam"""
    global recent_news_digest
    if not recent_news_digest:
        return

    try:
        lines = [
            "🌐 <b>THE FINAL TRADE — 2-HOUR GLOBAL DIGEST</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]

        # Pick up to 10 top headlines randomly to show recent events
        display_news = random.sample(recent_news_digest, min(len(recent_news_digest), 10))

        for item in display_news:
            lines.append(item)
            lines.append("")

        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "✝️ <i>The Final Trade — All glory to God.</i>"
        ])
        
        topic_id = int(TOPIC_NEWS) if TOPIC_NEWS and TOPIC_NEWS != "0" else None
        
        await bot.send_message(
            chat_id=int(GROUP_ID), 
            text="\n".join(lines), 
            parse_mode=ParseMode.HTML, 
            disable_web_page_preview=True,
            message_thread_id=topic_id
        )
        
        # Clear the digest so the next 2 hours has fresh events
        recent_news_digest.clear()
        
    except Exception as e:
        logger.error(f"2Hr Digest error: {e}")


async def auto_post_market_pulse(bot: Bot):
    """Market overview with Fear & Greed auto-posted to group."""
    try:
        coins = "bitcoin,ethereum,solana,binancecoin,terra-luna,terrausd"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        display = [
            ("bitcoin","BTC","🟠"), ("ethereum","ETH","🔷"), ("solana","SOL","🟣"),
            ("binancecoin","BNB","🟡"), ("terra-luna","LUNC","🔵"), ("terrausd","USTC","🟢"),
        ]

        fg_text = ""
        try:
            fg = requests.get(FEAR_GREED_API, timeout=5).json()['data'][0]
            val = int(fg['value'])
            fg_emoji = "😱" if val < 25 else "😰" if val < 50 else "😐" if val < 75 else "🤑"
            fg_text = f"{fg_emoji} <b>Fear & Greed:</b> {val}/100 ({fg['value_classification']})\n"
        except:
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
                lines.append(f"{emoji} <b>{symbol}</b>  {p_str}  {arrow}{change:+.1f}%")

        lines.extend([
            "",
            f"📈 <a href='https://www.weex.com/en?vipCode={WEEX_REF}'>Trade on WEEX</a>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "✝️ <i>The Final Trade — All glory to God</i>",
            "#TheFinalTrade #MarketPulse #crypto"
        ])

        topic_id = int(TOPIC_SIGNALS) if TOPIC_SIGNALS and TOPIC_SIGNALS != "0" else None

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
        print("ERROR: BOT_TOKEN not set.")
        exit(1)

    # Health server
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Health server on port 10000")

    # Auto-posting
    if GROUP_ID:
        threading.Thread(target=auto_post_loop, args=(BOT_TOKEN,), daemon=True).start()
        print(f"Auto-posting V3 armed for group {GROUP_ID}")
    else:
        print("No GROUP_ID — auto-posting disabled.")

    # Build app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # All command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("token", token_command))
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

    # Inline buttons
    app.add_handler(CallbackQueryHandler(button_callback))

    print("✝️ The Final Trade Bot V3 — All glory to God! LIVE.")
    app.run_polling()
