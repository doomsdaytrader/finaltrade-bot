import logging
import requests
import random
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from config import (
    GROUP_ID, TOPIC_SIGNALS, WEEX_REF, BYDFI_REF, BITUNIX_REF, BTCC_REF, KCEX_REF, COINGECKO_MARKETS
)
from telegram_commands import estimate_rsi

logger = logging.getLogger(__name__)

# Keep track of recently alerted coins
recent_alerts = []

# Affiliate categorization mapper
def get_exchange_for_coin(symbol, category):
    """
    Returns (Exchange Name, URL) based on the token category.
    """
    symbol = symbol.upper()
    blue_chips = ["BTC", "ETH", "XRP"]
    l1_utility = ["SOL", "ADA", "DOT", "AVAX", "LINK", "LUNC", "USTC", "MATIC", "ATOM", "NEAR"]

    if symbol in blue_chips:
        # BTCC for Blue Chips or BYDFI
        exchanges = [
            ("BTCC", f"https://www.btcc.com/en-US/register?inviteCode={BTCC_REF}"),
            ("BYDFi", f"https://partner.bydfi.com/register?vipCode={BYDFI_REF}"),
            ("WEEX", f"https://www.weex.com/en/spot/{symbol}_USDT?vipCode={WEEX_REF}")
        ]
        return random.choice(exchanges)

    elif symbol in l1_utility:
        # BYDFi or WEEX
        exchanges = [
            ("BYDFi", f"https://partner.bydfi.com/register?vipCode={BYDFI_REF}"),
            ("WEEX", f"https://www.weex.com/en/spot/{symbol}_USDT?vipCode={WEEX_REF}")
        ]
        return random.choice(exchanges)
    
    else:
        # Hot Spikes / Memes / Gainers / Losers -> Bitunix or KCEX
        exchanges = [
            ("Bitunix", f"https://www.bitunix.com/register?vipCode={BITUNIX_REF}"),
            ("Bitunix", f"https://www.bitunix.com/register?vipCode={BITUNIX_REF}"),
            ("KCEX", f"https://www.kcex.com/register?inviteCode={KCEX_REF}"),
            ("KCEX", f"https://www.kcex.com/register?inviteCode={KCEX_REF}")
        ]
        return random.choice(exchanges)


async def auto_post_hottest_tokens(bot: Bot):
    """
    Scans the Top 20 market cap tokens + Terra Ecosystem (LUNC/USTC) and
    posts a robust trading setup using the user's affiliate links.
    """
    global recent_alerts

    try:
        # Fetch Top 20 tokens by Market Cap
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=true&price_change_percentage=1h,24h"
        data = requests.get(url, timeout=15).json()

        # Specifically fetch Terra Tokens regardless of Top 20 rank
        terra_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=terra-luna,terrausd&sparkline=true&price_change_percentage=1h,24h"
        terra_data = requests.get(terra_url, timeout=15).json()

        if isinstance(data, list) and isinstance(terra_data, list):
            # Combine without duplicating if somehow terra enters top 20
            existing_ids = {c['id'] for c in data}
            for tc in terra_data:
                if tc['id'] not in existing_ids:
                    data.append(tc)
        
        if not data or not isinstance(data, list):
            return

        # Sort by 24h volatility (absolute change) to find the most exciting action
        valid_coins = [c for c in data if c.get('price_change_percentage_24h') is not None]
        valid_coins.sort(key=lambda x: abs(x['price_change_percentage_24h']), reverse=True)

        target_coin = None
        for c in valid_coins:
            if c['id'] not in recent_alerts:
                target_coin = c
                break
        
        # If all top cycled, clear history and start over
        if not target_coin and valid_coins:
            recent_alerts.clear()
            target_coin = valid_coins[0]

        if not target_coin:
            return

        # Update cache (keep last 12 to ensure rotation)
        recent_alerts.append(target_coin['id'])
        if len(recent_alerts) > 12:
            recent_alerts.pop(0)

        # Categorize
        if target_coin['price_change_percentage_24h'] >= 2:
            category = "🚀 BULLISH MOMENTUM ALERT"
            trade_dir = "LONG 🟢"
        elif target_coin['price_change_percentage_24h'] <= -2:
            category = "🩸 REVERSAL & DIP OPPORTUNITY"
            trade_dir = "SHORT 🔴"
        else:
            category = "⚖️ RANGE BOUND SCALP ZONES"
            trade_dir = "SCALP ⚪"

        # Extract data
        name = target_coin['name']
        symbol = target_coin['symbol'].upper()
        price = target_coin['current_price']
        change_24h = target_coin['price_change_percentage_24h']
        change_1h = target_coin.get('price_change_percentage_1h_in_currency', 0) or 0
        volume = target_coin['total_volume']
        market_cap = target_coin['market_cap']
        image_url = target_coin['image']
        sparkline = target_coin.get('sparkline_in_7d', {}).get('price', [])
        
        # Calculate RSI
        rsi = estimate_rsi(sparkline[-24:]) if len(sparkline) >= 14 else 50.0

        # Build trade setup logic
        if trade_dir == "LONG 🟢":
            entry_price = price * 0.985  # Buy on short dip
            take_profit = price * 1.05   # Target +5%
            stop_loss = price * 0.95     # Stop -5%
            leverage = "10x-20x"
            reason = "High volume influx / Bullish momentum surge."
        elif trade_dir == "SHORT 🔴":
            entry_price = price * 1.015  # Short on minor bounce
            take_profit = price * 0.95   # Target -5% down
            stop_loss = price * 1.05     # Stop +5%
            leverage = "5x-10x"
            reason = "RSI cooling down / Heavy distribution spotted."
        else:
            entry_price = price
            take_profit = price * 1.02
            stop_loss = price * 0.98
            leverage = "20x-50x (High Risk)"
            reason = "Consolidating. Play tight channels."

        # Fetch exchange for this token
        exchange_name, affiliate_link = get_exchange_for_coin(symbol, category)

        # Formatting
        p_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
        vol_str = f"${volume/1e9:,.2f}B" if volume >= 1e9 else f"${volume/1e6:,.1f}M"
        mc_str = f"${market_cap/1e9:,.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:,.1f}M"
        
        arrow = "🟢▲" if change_24h > 0 else "🔴▼"

        caption = (
            f"⚡ <b>{category} — {name} ({symbol})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Price:</b> {p_str}\n"
            f"{arrow} <b>24h Change:</b> {change_24h:+.2f}%\n"
            f"📈 <b>24h Volume:</b> {vol_str}\n"
            f"📊 <b>Market Cap:</b> {mc_str}\n"
            f"🧠 <b>AI RSI Status:</b> {rsi}\n\n"
            f"🎯 <b>AI TRADE SETUP ({trade_dir})</b>\n"
            f"┣ <b>Entry Range:</b> ${entry_price:,.5f}\n"
            f"┣ <b>Take Profit:</b> ${take_profit:,.5f}\n"
            f"┣ <b>Stop Loss:</b> ${stop_loss:,.5f}\n"
            f"┣ <b>Leverage:</b> {leverage}\n"
            f"┗ <b>Rationale:</b> {reason}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade</i> — <i>Always trade responsibly.</i>"
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
