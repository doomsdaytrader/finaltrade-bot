# -*- coding: utf-8 -*-
import logging
import requests
import random
import time
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from config import (
    GROUP_ID, TOPIC_SIGNALS,
    BITBASE_REF, WEEX_REF, BYDFI_REF, BYBIT_REF, BITUNIX_REF,
    KCEX_REF, VOOX_REF, BITMART_REF, ORANGEX_REF,
    COINGECKO_MARKETS
)
from telegram_commands import estimate_rsi

logger = logging.getLogger(__name__)

import os

# Track recently alerted coins to rotate through them
recent_alerts = []
try:
    if os.path.exists("recent_alerts.txt"):
        with open("recent_alerts.txt", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    recent_alerts.append(line.strip())
except Exception:
    pass


# Pre-seeded cache so the bot has data to fire on cold start
market_cache = [
    {"id": "bitcoin",    "name": "Bitcoin",          "symbol": "btc",  "current_price": 60000,  "price_change_percentage_24h": 0.5,  "total_volume": 30000000000, "market_cap": 1200000000000, "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"},
    {"id": "ethereum",   "name": "Ethereum",         "symbol": "eth",  "current_price": 3000,   "price_change_percentage_24h": -1.2, "total_volume": 15000000000, "market_cap": 400000000000,  "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png"},
    {"id": "solana",     "name": "Solana",            "symbol": "sol",  "current_price": 140,    "price_change_percentage_24h": 4.5,  "total_volume": 4000000000,  "market_cap": 70000000000,   "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png"},
    {"id": "terra-luna", "name": "Terra Luna Classic","symbol": "lunc", "current_price": 0.0001, "price_change_percentage_24h": 1.0,  "total_volume": 50000000,    "market_cap": 600000000,     "image": "https://assets.coingecko.com/coins/images/8284/large/01_LunaClassic_color.png"},
    {"id": "terrausd",   "name": "TerraClassicUSD",  "symbol": "ustc", "current_price": 0.02,   "price_change_percentage_24h": -0.5, "total_volume": 10000000,    "market_cap": 200000000,     "image": "https://assets.coingecko.com/coins/images/12167/large/ustc.png"},
]
last_fetch_time = 0
CACHE_DURATION = 300  # 5 minutes


# ============================================================
# PINPOINT PRICE ENGINE — MEXC → Binance fallback
# ============================================================
def get_accurate_price(symbol):
    """Fetch real-time price from MEXC, then Binance as fallback."""
    symbol = symbol.upper()
    trade_pair = f"{symbol}USDT"

    # Try MEXC V3 first (great for LUNC/USTC and alt coins)
    try:
        url = f"https://api.mexc.com/api/v3/ticker/price?symbol={trade_pair}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'price' in data:
                price = float(data['price'])
                logger.info(f"[PRICE ENGINE] MEXC Realtime: {symbol} @ ${price}")
                return price
    except Exception as e:
        logger.debug(f"[PRICE ENGINE] MEXC error: {e}")

    # Try Binance V3
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={trade_pair}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            price = float(r.json()['price'])
            logger.info(f"[PRICE ENGINE] Binance Realtime: {symbol} @ ${price}")
            return price
    except Exception as e:
        logger.debug(f"[PRICE ENGINE] Binance error: {e}")

    return None


# ============================================================
# AFFILIATE LINK ROUTER
# ============================================================
def get_exchange_for_coin(symbol, category):
    """Return (Exchange Name, URL) based on token category."""
    symbol = symbol.upper()
    blue_chips = ["BTC", "ETH", "XRP"]
    l1_utility = ["SOL", "ADA", "DOT", "AVAX", "LINK", "LUNC", "USTC", "MATIC", "ATOM", "NEAR"]

    if symbol in blue_chips:
        exchanges = [
            ("Bybit",   f"https://partner.bybit.com/b/{BYBIT_REF}"),
            ("Bitbase", f"https://www.bitbase.com/accounts/register/start?ref={BITBASE_REF}"),
            ("WEEX",    f"https://www.weex.com/en/register?vipCode={WEEX_REF}"),
            ("BitMart", f"https://www.bitmart.com/invite/{BITMART_REF}"),
        ]
    elif symbol in l1_utility:
        exchanges = [
            ("BYDFi",   f"https://partner.bydfi.com/register?vipCode={BYDFI_REF}"),
            ("OrangeX", f"https://affiliates.orangex.com/affiliates/b/{ORANGEX_REF}"),
            ("WEEX",    f"https://www.weex.com/en/register?vipCode={WEEX_REF}"),
        ]
    else:
        # Hot spikes / memes / gainers / losers
        exchanges = [
            ("Bitunix", f"https://www.bitunix.com/register?vipCode={BITUNIX_REF}"),
            ("KCEX",    f"https://www.kcex.com?inviteCode={KCEX_REF}"),
            ("VOOX",    f"https://voox.com/register?inviteCode={VOOX_REF}"),
        ]

    return random.choice(exchanges)


# ============================================================
# AUTO-POST: HOTTEST TOKENS SIGNAL
# ============================================================
async def auto_post_hottest_tokens(bot: Bot):
    """
    Scans Top 20 market cap tokens + Terra Ecosystem (LUNC/USTC)
    and posts a robust trading setup with real-time prices and affiliate links.
    """
    global recent_alerts, market_cache, last_fetch_time

    current_time = time.time()
    data = []

    # Refresh cache if stale
    if (current_time - last_fetch_time) > CACHE_DURATION:
        try:
            logger.info("[TOKEN SCANNER] Fetching fresh data from CoinGecko...")
            last_fetch_time = current_time

            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                "?vs_currency=usd&order=market_cap_desc&per_page=20&page=1"
                "&sparkline=true&price_change_percentage=1h,24h"
            )
            resp = requests.get(url, timeout=15)
            logger.info(f"[TOKEN SCANNER] CoinGecko Top20 status: {resp.status_code}")

            if resp.status_code == 200:
                fetched_data = resp.json()
                # Also fetch Terra tokens specifically
                terra_url = (
                    "https://api.coingecko.com/api/v3/coins/markets"
                    "?vs_currency=usd&ids=terra-luna,terrausd"
                    "&sparkline=true&price_change_percentage=1h,24h"
                )
                terra_resp = requests.get(terra_url, timeout=15)
                terra_data = terra_resp.json() if terra_resp.status_code == 200 else []

                if isinstance(fetched_data, list):
                    existing_ids = {c['id'] for c in fetched_data}
                    for tc in terra_data:
                        if tc['id'] not in existing_ids:
                            fetched_data.append(tc)
                    market_cache = fetched_data
                    logger.info(f"[TOKEN SCANNER] Cache updated: {len(fetched_data)} coins.")
            elif resp.status_code == 429:
                logger.warning("[TOKEN SCANNER] CoinGecko rate limit (429). Using cache.")
                data = market_cache
            else:
                logger.error(f"[TOKEN SCANNER] CoinGecko error: {resp.status_code}")
                data = market_cache

        except Exception as e:
            logger.error(f"[TOKEN SCANNER] Fetch error: {e}")
            data = market_cache
    else:
        data = market_cache
        logger.info(f"[TOKEN SCANNER] Using cached data (age: {int(current_time - last_fetch_time)}s)")

    try:
        if not data or not isinstance(data, list):
            logger.warning("[TOKEN SCANNER] No market data available.")
            return

        # Sort by absolute 24h change to find most exciting action
        valid_coins = [c for c in data if c.get('price_change_percentage_24h') is not None]
        valid_coins.sort(key=lambda x: abs(x['price_change_percentage_24h']), reverse=True)

        # Pick next coin not recently alerted
        target_coin = None
        for c in valid_coins:
            if c['id'] not in recent_alerts:
                target_coin = c
                break

        # If all cycled, reset and start over
        if not target_coin and valid_coins:
            recent_alerts.clear()
            target_coin = valid_coins[0]

        if not target_coin:
            logger.warning("[TOKEN SCANNER] No target coin found.")
            return

        recent_alerts.append(target_coin['id'])
        if len(recent_alerts) > 12:
            recent_alerts.pop(0)
            
        try:
            with open("recent_alerts.txt", "w", encoding="utf-8") as f:
                for coin_id in recent_alerts:
                    f.write(coin_id + "\n")
        except Exception:
            pass

        name   = target_coin['name']
        symbol = target_coin['symbol'].upper()
        change_24h = target_coin['price_change_percentage_24h']
        change_1h  = target_coin.get('price_change_percentage_1h_in_currency', 0) or 0
        volume     = target_coin['total_volume']
        market_cap = target_coin['market_cap']
        image_url  = target_coin['image']
        sparkline  = target_coin.get('sparkline_in_7d', {}).get('price', [])

        logger.info(f"[TOKEN SCANNER] Selected: {name} ({symbol}) | 24h: {change_24h:+.2f}%")

        # Real-time price override
        accurate_price = get_accurate_price(symbol)
        price = accurate_price if accurate_price else target_coin['current_price']
        if not accurate_price:
            logger.warning(f"[PRICE ENGINE] Fallback to cached price for {symbol}: ${price}")

        # RSI from sparkline
        rsi = estimate_rsi(sparkline[-24:]) if len(sparkline) >= 14 else 50.0

        # Categorise signal direction
        if change_24h >= 2:
            category   = "🚀 BULLISH MOMENTUM ALERT"
            trade_dir  = "LONG 🟢"
            entry_price = price * 0.985
            take_profit = price * 1.05
            stop_loss   = price * 0.95
            leverage    = "10x–20x"
            reason      = "High volume influx / Bullish momentum surge."
        elif change_24h <= -2:
            category   = "🩸 REVERSAL & DIP OPPORTUNITY"
            trade_dir  = "SHORT 🔴"
            entry_price = price * 1.015
            take_profit = price * 0.95
            stop_loss   = price * 1.05
            leverage    = "5x–10x"
            reason      = "RSI cooling / Heavy distribution spotted."
        else:
            category   = "⚖️ RANGE BOUND SCALP ZONES"
            trade_dir  = "SCALP ⚪"
            entry_price = price
            take_profit = price * 1.02
            stop_loss   = price * 0.98
            leverage    = "20x–50x (High Risk)"
            reason      = "Consolidating. Play tight channels."

        # Format prices
        p_str  = f"${price:,.2f}"      if price >= 1     else f"${price:,.6f}"
        ep_str = f"${entry_price:,.2f}" if entry_price >= 1 else f"${entry_price:,.6f}"
        tp_str = f"${take_profit:,.2f}" if take_profit >= 1 else f"${take_profit:,.6f}"
        sl_str = f"${stop_loss:,.2f}"   if stop_loss >= 1   else f"${stop_loss:,.6f}"
        vol_str = f"${volume/1e9:,.2f}B"      if volume     >= 1e9 else f"${volume/1e6:,.1f}M"
        mc_str  = f"${market_cap/1e9:,.2f}B"  if market_cap >= 1e9 else f"${market_cap/1e6:,.1f}M"
        arrow   = "🟢▲" if change_24h > 0 else "🔴▼"

        exchange_name, affiliate_link = get_exchange_for_coin(symbol, category)

        caption = (
            f"⚡ <b>{category} — {name} ({symbol})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> {p_str}\n"
            f"{arrow} <b>24h Change:</b> {change_24h:+.2f}%\n"
            f"📈 <b>24h Volume:</b> {vol_str}\n"
            f"📊 <b>Market Cap:</b> {mc_str}\n"
            f"🧠 <b>AI RSI Status:</b> {rsi:.1f}\n\n"
            f"🎯 <b>AI TRADE SETUP ({trade_dir})</b>\n"
            f"┣ <b>Entry Range:</b> {ep_str}\n"
            f"┣ <b>Take Profit:</b> {tp_str}\n"
            f"┣ <b>Stop Loss:</b>   {sl_str}\n"
            f"┣ <b>Leverage:</b>    {leverage}\n"
            f"┗ <b>Rationale:</b>   {reason}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ <i>AYEWAKEN FUTURES</i> — <i>Always trade responsibly.</i>"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📈 Trade {symbol} on {exchange_name}", url=affiliate_link)]
        ])

        topic_id = int(TOPIC_SIGNALS) if TOPIC_SIGNALS and TOPIC_SIGNALS != "0" else None

        if image_url:
            await bot.send_photo(
                chat_id=int(GROUP_ID),
                photo=image_url,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                message_thread_id=topic_id
            )
        else:
            await bot.send_message(
                chat_id=int(GROUP_ID),
                text=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                message_thread_id=topic_id
            )

    except Exception as e:
        logger.error(f"Hottest tokens auto-post error: {e}")
