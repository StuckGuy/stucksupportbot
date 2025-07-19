import os
import time
import logging
import asyncio
import random
from telegram import Update, ChatMemberUpdated
from telegram.constants import ChatAction  # ✅ FIXED
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, ChatMemberHandler
import openai

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Trigger keywords
BUY_TRIGGERS = ["where to buy", "how to buy", "buy stuck", "buy $stuck", "chart", "moonshot", "token", "$stuck"]
DEAD_TRIGGERS = ["dead", "rug", "abandoned", "no team", "still alive", "exit", "pull"]
ROADMAP_TRIGGERS = ["roadmap", "plans", "future", "milestone"]
UTILITY_TRIGGERS = ["utility", "use case", "purpose", "what does it do"]
TEAM_TRIGGERS = ["team", "devs", "developers", "who made"]
TAX_TRIGGERS = ["tax", "buy tax", "sell tax"]
WEBSITE_TRIGGERS = ["website", "site", "link", "official page"]
SCAM_PHRASES = ["dm", "promo", "partner", "collab", "shill", "call group", "inbox", "promotion", "reach out"]

# In-memory cache
cached_replies = {}

# Prompt template
BASE_PROMPT = (
    "You're Chad, the sarcastic, funny $STUCK community degen who helps in Telegram groups. "
    "You roast, meme, and explain things like a true crypto degen — never like a corporate bot. "
    "If asked about:\n"
    "- Buying: say $STUCK is *only* on Moonshot until $1M liquidity\n"
    "- If it's dead: act offended but reassure it's alive\n"
    "- Roadmap: joke that memes are the roadmap, but community strength is real\n"
    "- Utility: say the utility is coping through the bear and memeing\n"
    "- Team: say team is anonymous and vibes-based\n"
    "- Taxes: say 0/0 — we allergic to taxes\n"
    "- Website: it’s https://stillstuck.lol\n"
    "NEVER tell anyone to DM. Always reply publicly. Always end with: https://moonshot.com?ref=Xonkwkbt80"
    "\n\nUser: {question}\nChad:"
)

# Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.lower()

    # Delete scammy messages quietly
    if any(phrase in text for phrase in SCAM_PHRASES):
        try:
            await message.delete()
            logger.info("🚫 Deleted spam/scam.")
        except Exception as e:
            logger.warning(f"❌ Couldn't delete: {e}")
        return

    # Check if message matches any known triggers
    TRIGGER_CATEGORIES = BUY_TRIGGERS + DEAD_TRIGGERS + ROADMAP_TRIGGERS + UTILITY_TRIGGERS + TEAM_TRIGGERS + TAX_TRIGGERS + WEBSITE_TRIGGERS
    triggered = None
    for word in TRIGGER_CATEGORIES:
        if word in text:
            triggered = word
            break

    if not triggered:
        return  # Skip unrelated messages

    try:
        await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(2)
    except:
        pass

    # Use cached response
    if triggered in cached_replies:
        await message.reply_text(cached_replies[triggered])
        return

    # Generate reply via OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You're a sarcastic Telegram crypto degen named Chad who roasts and helps people in meme coin groups."},
                {"role": "user", "content": BASE_PROMPT.format(question=text)}
            ],
            max_tokens=160,
            temperature=0.85
        )
        reply = response.choices[0].message.content.strip()
        cached_replies[triggered] = reply
        await message.reply_text(reply)
    except Exception as e:
        logger.error(f"🔥 OpenAI error: {e}")
        await message.reply_text("Chad's passed out from too much cope. Try again later.")

# Handle new members joining
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        welcome_lines = [
            f"Yo {member.first_name}, welcome to $STUCK rehab. Check your baggage at the door 🧳💥",
            f"{member.first_name} just entered the stuck zone. No refunds. No roadmap. Just vibes 🚧",
            f"Welcome {member.first_name} — your coping journey starts now. Say gm and hold on tight 🫡"
        ]
        try:
            await context.bot.send_message(
                chat_id=update.chat_member.chat.id,
                text=random.choice(welcome_lines)
            )
        except Exception as e:
            logger.warning(f"Could not welcome user: {e}")

# Run bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    logger.info("🚀 StuckSupportBot (a.k.a. Chad) is live and vibin’...")
    app.run_polling()
