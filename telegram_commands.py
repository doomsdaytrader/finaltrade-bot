import requests
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Welcome to **The Final Trade**.\n"
        "First and foremost, **all glory goes to God** for this community and our success.\n\n"
        "I am your automated intelligence hub. I provide live data for:\n"
        "🔹 Crypto & Finance\n"
        "🔹 Survival & Geopolitics\n"
        "🔹 Whale Tracking\n\n"
        "Commands:\n"
        "/price <coin> - Live crypto price\n"
        "/news - Latest crypto news\n"
        "/survival - Geopolitics & Survival news\n"
        "/dashboard - Open the Mini App Terminal\n"
        "/lunc - LUNC specific insights\n"
        "/ustc - USTC specific insights"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a coin name. Example: `/price bitcoin`", parse_mode="Markdown")
        return

    coin = context.args[0].lower()
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        data = requests.get(url).json()

        if coin in data:
            price = data[coin]["usd"]
            await update.message.reply_text(f"📈 **{coin.upper()}** price: ${price}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Could not find price for {coin}.")
    except Exception as e:
        await update.message.reply_text("Error fetching price data.")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This will later query our FastAPI backend or just fetch directly
    await update.message.reply_text("📰 **Crypto News**: Check the Dashboard for real-time aggregation! (Feed syncing...)")

async def survival_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 **Survival & Geopolitics News**: Alert system active. Check dashboard for the latest feeds.")

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Users can tap a button for the mini app, or we provide the link
    msg = (
        "🖥️ **The Final Trade Terminal**\n"
        "Click the link below or the Mini App button to access the dashboard:\n"
        "🌐 https://finaltrade-dashboard-91me6lozz-irayecrypto-1565s-projects.vercel.app"
    )
    await update.message.reply_text(msg)

async def lunc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _fetch_specific_price(update, "terra-luna")

async def ustc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _fetch_specific_price(update, "terrausd")

async def _fetch_specific_price(update: Update, coin_id: str):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        data = requests.get(url).json()
        if coin_id in data:
            price = data[coin_id]["usd"]
            await update.message.reply_text(f"🔥 **{coin_id.upper()}** price: ${price}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("Error fetching asset info.")
