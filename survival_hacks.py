import logging
import random
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from config import GROUP_ID, TOPIC_SURVIVAL

logger = logging.getLogger(__name__)

HACKS = [
    {
        "title": "Water Purification: The 3-Filter Method",
        "content": "In a grid-down scenario, finding clean water is your #1 priority. If you only have access to muddy water, create a tripod filter: use three layers of cloth (like a t-shirt or bandana). \n\n1. Top layer: Rocks/gravel to catch large debris.\n2. Middle layer: Sand to catch fine particles.\n3. Bottom layer: Crushed charcoal (from your last fire) to absorb toxins and chemicals.\n\nAlways boil the filtered water for at least 1 minute before drinking to kill bacteria and viruses."
    },
    {
        "title": "Starting a Fire: The Battery & Steel Wool Hack",
        "content": "Matches get wet. Lighters run out of fluid. If you have a AA, AAA, or 9V battery and some fine steel wool (often found in kitchen cleaning pads), you have instant fire.\n\nTake the steel wool and gently rub it across the positive and negative terminals of the 9V battery (or hold a wire from positive to negative on a AA). It will instantly spark and ignite. Have your tinder bundle ready!"
    },
    {
        "title": "Faraday Cage: Protect Your Electronics from EMP",
        "content": "An EMP (Electromagnetic Pulse) or severe solar flare can fry all unshielded electronics, rendering phones, radios, and flashlights totally dead. \n\nYou can easily build a Faraday Cage using a galvanized steel trash can. Line the inside entirely with cardboard so no metal touches your devices. Store your emergency radio, walkie-talkies, and backup phones inside. Ensure the lid fits tightly so there are no gaps in the metal."
    },
    {
        "title": "Emergency Communications: The Baofeng UV-5R setup",
        "content": "When cell towers go down, ham radios are the only way to get intel. \n\nGet a cheap Baofeng UV-5R radio. Program it to receive NOAA weather frequencies (usually between 162.400 and 162.550 MHz) and local emergency frequencies. \n\nDon't transmit unless it's a life-or-death emergency, but listen constantly to know what's happening globally when the internet is entirely blacked out."
    },
    {
        "title": "Bleach for Water Purification",
        "content": "If you don't have means to boil water, you can purify it using regular, unscented household bleach (sodium hypochlorite, 5-9% concentration).\n\nUse 8 drops (about 1/8 teaspoon) of bleach per 1 gallon of clear water. If the water is cloudy, double the drops to 16. Stir and let it sit for exactly 30 minutes before drinking. It should have a faint chlorine smell—if it doesn't, repeat the dose."
    },
    {
        "title": "DIY Emergency Heater (Crisco + String)",
        "content": "Power grids can fail during extreme winter storms. If you have no heat, a simple container of Crisco (or any solid vegetable shortening) can save your life.\n\nInsert a cotton string, wick, or tightly rolled paper towel straight down to the bottom of the tub. Light the top. A standard tub of Crisco will burn like a clean candle for over 72 hours continuously, providing enough heat to warm a small enclosed room and light your space."
    },
    {
        "title": "The Rule of 3s in Survival",
        "content": "Whenever panic sets in, remember the Rule of 3s to prioritize your actions. You can survive:\n\n1. 3 Minutes without air / in icy water.\n2. 3 Hours without shelter in harsh environments (extreme cold/heat).\n3. 3 Days without water.\n4. 3 Weeks without food.\n\nFocus on shelter and water first. Do not waste energy hunting or foraging until your shelter and water needs are absolutely secured."
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
