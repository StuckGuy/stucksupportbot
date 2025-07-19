import os
import logging
import random
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    ChatMemberHandler,
    filters,
)
import openai

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Triggers
BUY_TRIGGERS = ["where to buy", "how to buy", "buy $stuck", "chart", "moonshot", "token", "$stuck"]
DEAD_TRIGGERS = ["dead", "rug", "abandoned", "no team", "still alive", "exit", "pull"]
ROADMAP_TRIGGERS = ["roadmap", "plans", "future", "milestone"]
UTILITY_TRIGGERS = ["utility", "use case", "purpose", "what does it do"]
TEAM_TRIGGERS = ["team", "devs", "developers", "who made"]
TAX_TRIGGERS = ["tax", "buy tax", "sell tax"]
WEBSITE_TRIGGERS = ["website", "site", "link", "official page"]
SCAM_PHRASES = ["dm", "promo", "partner", "collab", "shill", "call group", "inbox", "promotion", "reach out"]

# Memory cache
cached_replies = {}

# Welcome message
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        if not member.is_bot:
            await update.effective_chat.send_message(f"👋 Welcome {member.full_name}! You’re now part of the $STUCK family.")

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.from_user.is_bot:
        return

    text = update.message.text.lower()
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Ignore bots
    if update.message.from_user.is_bot:
        return

    # Delete scam phrases quietly
    if any(trigger in text for trigger in SCAM_PHRASES):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            return
        except Exception:
            return

    # Generate replies
    if text in cached_replies:
        await update.message.reply_text(cached_replies[text])
        return

    for trigger_list in [BUY_TRIGGERS, DEAD_TRIGGERS, ROADMAP_TRIGGERS, UTILITY_TRIGGERS, TEAM_TRIGGERS, TAX_TRIGGERS, WEBSITE_TRIGGERS]:
        if any(trigger in text for trigger in trigger_list):
            response = generate_reply(text)
            cached_replies[text] = response
            await update.message.reply_text(response)
            return

# Generate a fake GPT-style reply
def generate_reply(text):
    return (
        "😂 $STUCK is stuck AF... but it’s the best kind of stuck.\n\n"
        "✅ No promises\n🚫 No dev tokens\n🧠 Just vibes\n\n"
        "Join the community. Track it. Laugh. Moon? Maybe.\nhttps://moonshot.com?ref=Xonkwkbt80"
    )

# Start bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    logger.info("📢 StuckSupportBot (a.k.a. Chad) is live and vibin’...")
    app.run_polling()
