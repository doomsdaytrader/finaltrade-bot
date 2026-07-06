# -*- coding: utf-8 -*-
import logging
import requests
import random
import time
import os
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

# ============================================================
# PERSISTENT RECENTLY-ALERTED MEMORY
# ============================================================
recent_alerts = []
try:
    if os.path.exists("recent_alerts.txt"):
        with open("recent_alerts.txt", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    recent_alerts.append(line.strip())
except Exception:
    pass

# ============================================================
# PRE-SEEDED CACHE — Cold-start fallback data
# ============================================================
market_cache = [
    {"id": "bitcoin",    "name": "Bitcoin",           "symbol": "btc",  "current_price": 63000,  "price_change_percentage_24h": 1.2,  "total_volume": 32000000000, "market_cap": 1230000000000, "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png"},
    {"id": "ethereum",   "name": "Ethereum",          "symbol": "eth",  "current_price": 3400,   "price_change_percentage_24h": -0.8, "total_volume": 14000000000, "market_cap": 410000000000,  "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png"},
    {"id": "solana",     "name": "Solana",             "symbol": "sol",  "current_price": 145,    "price_change_percentage_24h": 4.5,  "total_volume": 4200000000,  "market_cap": 72000000000,   "image": "https://assets.coingecko.com/coins/images/4128/large/solana.png"},
    {"id": "terra-luna", "name": "Terra Luna Classic", "symbol": "lunc", "current_price": 0.0001, "price_change_percentage_24h": 2.1,  "total_volume": 60000000,    "market_cap": 620000000,     "image": "https://assets.coingecko.com/coins/images/8284/large/01_LunaClassic_color.png"},
    {"id": "terrausd",   "name": "TerraClassicUSD",   "symbol": "ustc", "current_price": 0.021,  "price_change_percentage_24h": -0.3, "total_volume": 12000000,    "market_cap": 210000000,     "image": "https://assets.coingecko.com/coins/images/12167/large/ustc.png"},
]
last_fetch_time  = 0
CACHE_DURATION   = 300  # 5 minutes


# ============================================================
# PINPOINT PRICE ENGINE — MEXC → Binance fallback
# ============================================================
def get_accurate_price(symbol):
    symbol = symbol.upper()
    trade_pair = f"{symbol}USDT"
    for exchange, url_tpl in [
        ("MEXC",    f"https://api.mexc.com/api/v3/ticker/price?symbol={trade_pair}"),
        ("Binance", f"https://api.binance.com/api/v3/ticker/price?symbol={trade_pair}"),
    ]:
        try:
            r = requests.get(url_tpl, timeout=5)
            if r.status_code == 200:
                data = r.json()
                price = float(data.get("price", 0))
                if price > 0:
                    logger.info(f"[PRICE ENGINE] {exchange}: {symbol} @ ${price}")
                    return price
        except Exception as e:
            logger.debug(f"[PRICE ENGINE] {exchange} error: {e}")
    return None


# ============================================================
# AFFILIATE LINK ROUTER
# ============================================================
def get_exchange_for_coin(symbol):
    symbol = symbol.upper()
    blue_chips  = ["BTC", "ETH", "XRP", "BNB"]
    l1_utility  = ["SOL", "ADA", "DOT", "AVAX", "LINK", "LUNC", "USTC", "MATIC", "ATOM", "NEAR"]

    if symbol in blue_chips:
        return random.choice([
            ("Bybit",   f"https://partner.bybit.com/b/{BYBIT_REF}"),
            ("Bitbase", f"https://www.bitbase.com/accounts/register/start?ref={BITBASE_REF}"),
            ("WEEX",    f"https://www.weex.com/en/register?vipCode={WEEX_REF}"),
            ("BitMart", f"https://www.bitmart.com/invite/{BITMART_REF}"),
        ])
    elif symbol in l1_utility:
        return random.choice([
            ("BYDFi",   f"https://partner.bydfi.com/register?vipCode={BYDFI_REF}"),
            ("OrangeX", f"https://affiliates.orangex.com/affiliates/b/{ORANGEX_REF}"),
            ("WEEX",    f"https://www.weex.com/en/register?vipCode={WEEX_REF}"),
        ])
    else:
        return random.choice([
            ("Bitunix", f"https://www.bitunix.com/register?vipCode={BITUNIX_REF}"),
            ("KCEX",    f"https://www.kcex.com?inviteCode={KCEX_REF}"),
            ("VOOX",    f"https://voox.com/register?inviteCode={VOOX_REF}"),
        ])


# ============================================================
# SMART TRADE SETUP — Multi-level TP, Volatility-based SL
# ============================================================
def build_trade_setup(symbol, price, change_24h, rsi, volume, avg_volume_est):
    """
    Returns a structured trade setup with 3-tier TP and volatility-adjusted SL.
    Coins are categorised by their risk/volatility profile.
    """
    symbol = symbol.upper()

    # Determine volatility profile
    if symbol in ["LUNC", "USTC"]:
        profile = "micro"     # Very high volatility micro-cap
    elif symbol in ["BTC", "ETH"]:
        profile = "bluechip"  # Low-medium volatility
    elif symbol in ["SOL", "BNB", "ADA", "DOT", "AVAX", "LINK", "MATIC", "ATOM"]:
        profile = "midcap"    # Medium volatility
    else:
        profile = "altcoin"   # High volatility

    # Determine volume spike (if current vol is 1.5x the estimated average, it's spiking)
    vol_spike = volume > avg_volume_est * 1.5

    # RSI interpretation
    if rsi >= 70:
        rsi_label = "🔴 OVERBOUGHT — caution on longs"
    elif rsi <= 30:
        rsi_label = "🟢 OVERSOLD — watch for reversal"
    elif rsi >= 55:
        rsi_label = "🟡 BULLISH BIAS"
    elif rsi <= 45:
        rsi_label = "🟡 BEARISH BIAS"
    else:
        rsi_label = "⚪ NEUTRAL"

    # Signal direction
    if change_24h >= 3 or (change_24h >= 1.5 and vol_spike):
        direction = "LONG"
        emoji     = "🚀 BULLISH BREAKOUT"
    elif change_24h <= -3 or (change_24h <= -1.5 and vol_spike):
        direction = "SHORT / WAIT"
        emoji     = "🩸 BEARISH PRESSURE"
    else:
        direction = "SCALP"
        emoji     = "⚖️ RANGE-BOUND OPPORTUNITY"

    # --- Build levels based on profile ---
    if profile == "micro":
        # LUNC/USTC: Wide targets, high reward
        if direction == "LONG":
            entry  = price * 0.975
            tp1    = price * 1.15   # +15%
            tp2    = price * 1.30   # +30%
            tp3    = price * 1.50   # +50%
            sl     = price * 0.88   # -12% wide stop (micro-cap noise)
            lev    = "5x–15x"
            rationale = "Strong community volume detected. Terra Ecosystem move in play."
        elif direction == "SHORT / WAIT":
            entry  = price * 1.025
            tp1    = price * 0.88
            tp2    = price * 0.75
            tp3    = price * 0.65
            sl     = price * 1.12
            lev    = "3x–10x"
            rationale = "Distribution phase. Wait for support confirmation before re-entry."
        else:
            entry  = price
            tp1    = price * 1.12
            tp2    = price * 1.25
            tp3    = price * 1.40
            sl     = price * 0.90
            lev    = "3x–10x"
            rationale = "Accumulation zone. Small positions while range holds."

    elif profile == "bluechip":
        # BTC/ETH: Tighter but reliable levels
        if direction == "LONG":
            entry  = price * 0.990
            tp1    = price * 1.03   # +3%
            tp2    = price * 1.07   # +7%
            tp3    = price * 1.12   # +12%
            sl     = price * 0.955  # -4.5%
            lev    = "10x–25x"
            rationale = "Institutional momentum. Volume confirms buying pressure."
        elif direction == "SHORT / WAIT":
            entry  = price * 1.010
            tp1    = price * 0.97
            tp2    = price * 0.93
            tp3    = price * 0.89
            sl     = price * 1.045
            lev    = "5x–15x"
            rationale = "Macro headwinds. RSI overextended — watch for retest of support."
        else:
            entry  = price
            tp1    = price * 1.025
            tp2    = price * 1.05
            tp3    = price * 1.08
            sl     = price * 0.965
            lev    = "15x–30x"
            rationale = "Consolidating below key resistance. Tight scalp zone."

    elif profile == "midcap":
        if direction == "LONG":
            entry  = price * 0.982
            tp1    = price * 1.07   # +7%
            tp2    = price * 1.15   # +15%
            tp3    = price * 1.25   # +25%
            sl     = price * 0.93   # -7%
            lev    = "5x–20x"
            rationale = "L1 momentum building. Watch BTC for confirmation."
        elif direction == "SHORT / WAIT":
            entry  = price * 1.018
            tp1    = price * 0.93
            tp2    = price * 0.86
            tp3    = price * 0.80
            sl     = price * 1.07
            lev    = "5x–15x"
            rationale = "Fading after rejection from resistance. Risk-off environment."
        else:
            entry  = price
            tp1    = price * 1.06
            tp2    = price * 1.12
            tp3    = price * 1.20
            sl     = price * 0.935
            lev    = "10x–20x"
            rationale = "Low-volatility range. Scale in on dips toward support."

    else:  # altcoin
        if direction == "LONG":
            entry  = price * 0.978
            tp1    = price * 1.10
            tp2    = price * 1.22
            tp3    = price * 1.38
            sl     = price * 0.91   # -9%
            lev    = "3x–10x"
            rationale = "Altcoin momentum spike. High risk — small position sizing."
        elif direction == "SHORT / WAIT":
            entry  = price * 1.022
            tp1    = price * 0.91
            tp2    = price * 0.82
            tp3    = price * 0.74
            sl     = price * 1.09
            lev    = "3x–8x"
            rationale = "Altcoin dumping. Wait for clear base before long re-entry."
        else:
            entry  = price
            tp1    = price * 1.08
            tp2    = price * 1.18
            tp3    = price * 1.30
            sl     = price * 0.92
            lev    = "5x–12x"
            rationale = "Range-bound. Only trade confirmed breakouts from this zone."

    vol_spike_note = "⚡ VOLUME SPIKE DETECTED — elevated conviction." if vol_spike else ""

    return {
        "direction": direction,
        "emoji":     emoji,
        "entry":     entry,
        "tp1":       tp1,
        "tp2":       tp2,
        "tp3":       tp3,
        "sl":        sl,
        "leverage":  lev,
        "rationale": rationale,
        "rsi_label": rsi_label,
        "vol_spike": vol_spike_note,
        "profile":   profile,
    }


def fmt(price):
    """Format any crypto price as a clean, human-readable string."""
    if price == 0:
        return "$0.00"
    elif price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:,.3f}"
    elif price >= 0.01:
        return f"${price:,.4f}"
    elif price >= 0.001:
        return f"${price:,.5f}"
    elif price >= 0.0001:
        return f"${price:,.6f}"
    else:
        # Micro-cap: show 8 decimal places, NEVER scientific notation
        return f"${price:.8f}"


# ============================================================
# AUTO-POST: HOTTEST TOKENS SIGNAL
# ============================================================
async def auto_post_hottest_tokens(bot: Bot, force_symbol=None, exclude_symbols=None):
    """
    Posts a premium AI trade signal. Use force_symbol to target a specific coin.
    Use exclude_symbols (set of str) to skip specific coins.
    """
    global recent_alerts, market_cache, last_fetch_time

    current_time = time.time()
    data = []

    # Refresh market cache
    if (current_time - last_fetch_time) > CACHE_DURATION:
        try:
            logger.info("[TOKEN SCANNER] Fetching fresh data from CoinGecko...")
            last_fetch_time = current_time

            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                "?vs_currency=usd&order=market_cap_desc&per_page=25&page=1"
                "&sparkline=true&price_change_percentage=1h,24h"
            )
            resp = requests.get(url, timeout=15)
            logger.info(f"[TOKEN SCANNER] CoinGecko status: {resp.status_code}")

            if resp.status_code == 200:
                fetched = resp.json()
                # Ensure Terra tokens are always present
                terra_url = (
                    "https://api.coingecko.com/api/v3/coins/markets"
                    "?vs_currency=usd&ids=terra-luna,terrausd"
                    "&sparkline=true&price_change_percentage=1h,24h"
                )
                terra_resp = requests.get(terra_url, timeout=15)
                terra_data = terra_resp.json() if terra_resp.status_code == 200 else []

                if isinstance(fetched, list):
                    existing_ids = {c["id"] for c in fetched}
                    for tc in terra_data:
                        if tc["id"] not in existing_ids:
                            fetched.append(tc)
                    market_cache = fetched
                    logger.info(f"[TOKEN SCANNER] Cache updated: {len(fetched)} coins.")
            elif resp.status_code == 429:
                logger.warning("[TOKEN SCANNER] CoinGecko rate limit. Using cache.")
                data = market_cache
            else:
                data = market_cache
        except Exception as e:
            logger.error(f"[TOKEN SCANNER] Fetch error: {e}")
            data = market_cache
    else:
        data = market_cache

    if not data:
        data = market_cache

    try:
        if not data or not isinstance(data, list):
            logger.warning("[TOKEN SCANNER] No data.")
            return

        valid_coins = [c for c in data if c.get("price_change_percentage_24h") is not None]

        target_coin = None

        # Force a specific symbol — fetch directly if not in cache
        if force_symbol:
            for c in valid_coins:
                if c["symbol"].lower() == force_symbol.lower():
                    target_coin = c
                    break

            if not target_coin:
                # Directly fetch the forced coin from CoinGecko
                cg_id_map = {
                    "lunc": "terra-luna", "ustc": "terrausd",
                    "btc": "bitcoin", "eth": "ethereum",
                    "sol": "solana", "bnb": "binancecoin"
                }
                cg_id = cg_id_map.get(force_symbol.lower(), force_symbol.lower())
                try:
                    direct_url = (
                        f"https://api.coingecko.com/api/v3/coins/markets"
                        f"?vs_currency=usd&ids={cg_id}"
                        f"&sparkline=true&price_change_percentage=1h,24h"
                    )
                    dr = requests.get(direct_url, timeout=10)
                    if dr.status_code == 200 and dr.json():
                        target_coin = dr.json()[0]
                        logger.info(f"[TOKEN SCANNER] Direct fetch for {force_symbol.upper()} succeeded.")
                    else:
                        logger.warning(f"[TOKEN SCANNER] Direct fetch for {force_symbol.upper()} failed ({dr.status_code}).")
                except Exception as e:
                    logger.error(f"[TOKEN SCANNER] Direct fetch error for {force_symbol}: {e}")

        # General selection — exclude specified + recently posted
        if not target_coin:
            candidates = [c for c in valid_coins
                          if (not exclude_symbols or
                              (c["symbol"].lower() not in exclude_symbols and
                               c["id"] not in exclude_symbols))
                          and c["id"] not in recent_alerts]
            candidates.sort(key=lambda x: abs(x["price_change_percentage_24h"]), reverse=True)

            if candidates:
                target_coin = candidates[0]
            elif valid_coins:
                recent_alerts.clear()
                target_coin = valid_coins[0]

        if not target_coin:
            logger.warning("[TOKEN SCANNER] No target coin found.")
            return

        # Update rotation memory (skip for forced symbols)
        if not force_symbol:
            recent_alerts.append(target_coin["id"])
            if len(recent_alerts) > 15:
                recent_alerts.pop(0)
            try:
                with open("recent_alerts.txt", "w", encoding="utf-8") as f:
                    for coin_id in recent_alerts:
                        f.write(coin_id + "\n")
            except Exception:
                pass

        name       = target_coin["name"]
        symbol     = target_coin["symbol"].upper()
        change_24h = target_coin["price_change_percentage_24h"]
        change_1h  = target_coin.get("price_change_percentage_1h_in_currency", 0) or 0
        volume     = target_coin["total_volume"]
        market_cap = target_coin["market_cap"]
        image_url  = target_coin["image"]
        sparkline  = target_coin.get("sparkline_in_7d", {}).get("price", [])

        logger.info(f"[TOKEN SCANNER] Selected: {name} ({symbol}) | 24h: {change_24h:+.2f}%")

        # Real-time price
        accurate_price = get_accurate_price(symbol)
        price = accurate_price if accurate_price else target_coin["current_price"]

        # RSI from sparkline
        rsi = estimate_rsi(sparkline[-24:]) if len(sparkline) >= 14 else 50.0

        # Estimated average volume for spike detection (rough heuristic: 30% of market cap)
        avg_volume_est = market_cap * 0.007

        # Build professional trade setup
        setup = build_trade_setup(symbol, price, change_24h, rsi, volume, avg_volume_est)

        # Formatting
        vol_str = f"${volume/1e9:,.2f}B"  if volume     >= 1e9 else f"${volume/1e6:,.1f}M"
        mc_str  = f"${market_cap/1e9:,.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:,.1f}M"
        arrow   = "🟢▲" if change_24h > 0 else "🔴▼"
        change_1h_str = f"{change_1h:+.2f}%" if change_1h else "N/A"

        vol_spike_line = f"\n{setup['vol_spike']}" if setup["vol_spike"] else ""

        caption = (
            f"⚡ <b>{setup['emoji']} — {name} ({symbol})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> {fmt(price)}\n"
            f"{arrow} <b>24h Change:</b> {change_24h:+.2f}%  |  <b>1h:</b> {change_1h_str}\n"
            f"📈 <b>24h Volume:</b> {vol_str}\n"
            f"📊 <b>Market Cap:</b> {mc_str}\n"
            f"🧠 <b>RSI (14):</b> {rsi:.1f} — {setup['rsi_label']}{vol_spike_line}\n\n"
            f"🎯 <b>AI TRADE SETUP — {setup['direction']}</b>\n"
            f"┣ <b>Entry Zone:</b> {fmt(setup['entry'])}\n"
            f"┣ <b>TP1 (Conservative):</b> {fmt(setup['tp1'])}\n"
            f"┣ <b>TP2 (Target):</b>       {fmt(setup['tp2'])}\n"
            f"┣ <b>TP3 (Moon Bag):</b>     {fmt(setup['tp3'])}\n"
            f"┣ <b>Stop Loss:</b>          {fmt(setup['sl'])}\n"
            f"┣ <b>Leverage:</b>           {setup['leverage']}\n"
            f"┗ <b>Rationale:</b> {setup['rationale']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>Not financial advice. Manage your risk. Use stop losses.</i>\n"
            f"✍️ <i>AYEWAKEN FUTURES — All glory to God</i>"
        )

        exchange_name, affiliate_link = get_exchange_for_coin(symbol)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📈 Trade {symbol} on {exchange_name}", url=affiliate_link)]
        ])

        topic_id = int(TOPIC_SIGNALS) if TOPIC_SIGNALS and TOPIC_SIGNALS != "0" else None

        if image_url:
            await bot.send_photo(
                chat_id=int(GROUP_ID), photo=image_url,
                caption=caption, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, message_thread_id=topic_id
            )
        else:
            await bot.send_message(
                chat_id=int(GROUP_ID), text=caption,
                parse_mode=ParseMode.HTML, reply_markup=keyboard,
                message_thread_id=topic_id
            )

    except Exception as e:
        logger.error(f"auto_post_hottest_tokens error: {e}")
