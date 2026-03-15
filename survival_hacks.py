import logging
import random
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from config import GROUP_ID, TOPIC_SURVIVAL

logger = logging.getLogger(__name__)

HACKS = [
    {
        "title": "Water Purification: The 3-Filter Method",
        "content": "In a grid-down scenario, clean water is priority #1. If you only have muddy water, create a tripod filter: use three layers of cloth (like a t-shirt or bandana). \n\n1. Top layer: Rocks/gravel to catch large debris.\n2. Middle layer: Sand to catch fine particles.\n3. Bottom layer: Crushed charcoal (from your last fire) to absorb toxins.\n\nAlways boil the filtered water for 1 minute before drinking."
    },
    {
        "title": "Starting a Fire: Battery & Steel Wool",
        "content": "Matches get wet. Lighters run out of fluid. If you have a AA, AAA, or 9V battery and fine steel wool (often found in kitchens), you have instant fire.\n\nRub the steel wool gently across the positive and negative terminals of the battery. It will instantly spark and ignite. Have your tinder bundle ready!"
    },
    {
        "title": "Faraday Cage: Defeat EMPs",
        "content": "An EMP (Electromagnetic Pulse) or severe solar flare will fry all unshielded electronics, rendering phones, radios, and flashlights dead. \n\nBuild a Faraday Cage using a galvanized steel trash can. Line the inside completely with cardboard so NO metal touches your devices. Store your emergency radio, walkie-talkies, and crypto hardware wallets inside. Ensure the lid fits tightly."
    },
    {
        "title": "Emergency Comms: The Baofeng UV-5R",
        "content": "When cell towers go down, ham radios are the only way to get intel. \n\nGet a cheap Baofeng UV-5R radio. Program it to receive NOAA weather frequencies (162.400 - 162.550 MHz) and local emergency frequencies. \n\nDon't transmit unless it's a life-or-death emergency, but listen constantly to know what's happening globally when the internet is entirely blacked out."
    },
    {
        "title": "Bleach for Water Purification",
        "content": "If you cannot boil water, purify it using regular, unscented household bleach (sodium hypochlorite, 5-9% concentration).\n\nUse 8 drops (1/8 teaspoon) per 1 gallon of clear water. If clouded, double to 16 drops. Stir and let sit for exactly 30 minutes. It should have a faint chlorine smell—if not, repeat."
    },
    {
        "title": "DIY Emergency Heater (Crisco + String)",
        "content": "Power grids fail during extreme winter storms. A simple container of Crisco (solid vegetable shortening) can save your life.\n\nInsert a cotton string or tightly rolled paper towel straight down to the bottom of the tub. Light the top. A standard tub of Crisco will burn like a clean candle for over 72 HOURS continuously, heating a small enclosed room."
    },
    {
        "title": "The Rule of 3s in Survival",
        "content": "Whenever panic sets in, remember the Rule of 3s to prioritize actions. You survive:\n\n1. 3 Minutes without air / in icy water.\n2. 3 Hours without shelter in harsh environments.\n3. 3 Days without water.\n4. 3 Weeks without food.\n\nFocus on shelter and water first. Do not waste energy hunting until shelter/water are secured."
    },
    # --- NEW TACTICAL & CRYPTO-SURVIVAL HACKS ---
    {
        "title": "Grid-Down Wealth: The Hardware Wallet Decoy",
        "content": "In a total economic collapse or hyperinflation event, digital assets (BTC, ETH, stablecoins) stored on cold wallets (Ledger, Trezor) become extremely valuable.\n\nTACTIC: Keep a 'Decoy Wallet' with a small amount of crypto on your person if traveling through hostile zones. Hide your primary 'Vault Wallet' deep in your gear, wrapped in foil and sealed, protected by a passphrase you memorize but never write down."
    },
    {
        "title": "Barter Trading: Stockpiling High-Value Micro-Items",
        "content": "When fiat currency completely collapses, you cannot trade a gold bar for a loaf of bread. You need fractional liquidity. \n\nStockpile these high-velocity barter items now:\n- Mini Bic Lighters\n- Airline bottles of cheap vodka / whiskey\n- .22LR Ammunition (the ultimate post-fiat currency)\n- Travel-sized antibiotics and pain killers\n- Instant coffee packets"
    },
    {
        "title": "Digital Go-Bag: Encrypted USB Drive",
        "content": "Physical documents burn or get confiscated at borders. You need a Digital Go-Bag.\n\nBuy a rugged, waterproof USB drive. Use VeraCrypt to create a massive hidden, encrypted volume. \nStore inside: High-res scans of Passports, IDs, Land Deeds, Medical Records, family photos, and a text file containing exactly ONE set of 24-word seed phrases for an emergency crypto rescue wallet. Wear the USB on a titanium necklace."
    },
    {
        "title": "Tactical OpSec: The Gray Man Protocol",
        "content": "During civil unrest or martial law, looking like a 'Prepper' or wearing tactical gear makes you a primary target. \n\nAdopt the Gray Man philosophy: Wear muted, neutral colors. Use a nondescript standard hiking backpack, not a Molle military bag. Do not make eye contact, walk with purpose but not aggression, and never broadcast what supplies or crypto wealth you hold."
    },
    {
        "title": "Mesh Networks: Offline Crypto Trading",
        "content": "If the government shuts off the internet, localized transactions can still occur. \n\nLearn how to use goTenna Mesh devices or LoRaWAN networks. You can sign a Bitcoin transaction completely offline on a hardware wallet, and broadcast it over a radio mesh network to a node miles away that still has satellite connectivity (like Starlink), bypassing local internet blackouts entirely."
    },
    {
        "title": "Advanced Medical: Post-Trauma Superglue",
        "content": "In a grid-down scenario where hospitals are offline or overrun, treating lacerations quickly is critical to prevent fatal infections.\n\nStandard medical cyanoacrylate (or regular Superglue in a pinch) can be used to instantly close deep, clean cuts that would normally require stitches. Clean the wound heavily with iodine, pinch the skin together, and glue the surface (never glue deep *inside* the wound)."
    }
]

async def auto_post_survival_hack(bot: Bot):
    """Posts a random survival hack."""
    try:
        if not GROUP_ID:
            return

        hack = random.choice(HACKS)
        
        msg = (
            f"🛡️ <b>SURVIVAL INTEL / TACTICAL HACK</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🧠 <b>{hack['title']}</b>\n\n"
            f"{hack['content']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✝️ <i>The Final Trade — Be Prepared.</i>"
        )
        
        topic_id = int(TOPIC_SURVIVAL) if TOPIC_SURVIVAL and TOPIC_SURVIVAL != "0" else None
        
        await bot.send_message(
            chat_id=int(GROUP_ID),
            text=msg,
            parse_mode=ParseMode.HTML,
            message_thread_id=topic_id
        )
    except Exception as e:
        logger.error(f"Survival hack auto-post error: {e}")
