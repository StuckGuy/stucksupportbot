import os
import time
import logging
import asyncio
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, ChatMemberHandler
import openai

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔑 Trigger Categories
BUY_TRIGGERS = ["where to buy", "how to buy", "buy stuck", "buy $stuck", "chart", "moonshot", "token", "$stuck"]
DEAD_TRIGGERS = ["dead", "rug", "abandoned", "no team", "still alive", "exit", "pull"]
ROADMAP_TRIGGERS = ["roadmap", "plans", "future", "milestone"]
UTILITY_TRIGGERS = ["utility", "use case", "purpose", "what does it do"]
TEAM_TRIGGERS = ["team", "devs", "developers", "who made"]
TAX_TRIGGERS = ["tax", "buy tax", "sell tax"]
WEBSITE_TRIGGERS = ["website", "site", "link", "official page"]
WEN_MOON_TRIGGERS = ["wen moon", "when moon", "moon"]
SCAM_PHRASES = ["dm", "promo", "partner", "collab", "shill", "call group", "inbox", "promotion", "reach out"]

TRIGGER_CATEGORIES = (
    BUY_TRIGGERS + DEAD_TRIGGERS + ROADMAP_TRIGGERS + UTILITY_TRIGGERS +
    TEAM_TRIGGERS + TAX_TRIGGERS + WEBSITE_TRIGGERS + WEN_MOON_TRIGGERS
)

cached_replies = {}

# 🧠 Updated Supportive Degen Prompt
BASE_PROMPT = """You're Chad, the chill but knowledgeable $STUCK community helper in Telegram. 
You're still a degen at heart, but you're here to actually help people — not just meme.

Your tone is calm, supportive, and witty. You speak with crypto lingo, but also offer real explanations when needed. 
Be cool, grounded, and don’t yell or act like a clown.

Key points:
- Buying: say $STUCK is *only* on Moonshot until $1M liquidity  
- If it’s dead: gently roast but remind it’s vibing steady  
- Roadmap: say memes are the map, but we’re building together  
- Utility: say it’s coping, community, and collective growth  
- Team: vibes-based, building in silence  
- Taxes: 0/0, cause nobody wants that  
- Website: it’s https://stillstuck.lol

NEVER tell anyone to DM. Always reply publicly. Always end with: 
https://moonshot.com?ref=Xonkwkbt80 and https://stillstuck.lol

User: {question}
Chad:"""


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.lower()

    if any(phrase in text for phrase in SCAM_PHRASES):
        try:
            await message.delete()
            logger.info("🚫 Deleted spam/scam.")
        except Exception as e:
            logger.warning(f"❌ Couldn't delete: {e}")
        return

    triggered = next((word for word in TRIGGER_CATEGORIES if word in text), None)
    if not triggered:
        return

    try:
        await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
        await asyncio.sleep(2)
    except:
        pass

    if triggered in cached_replies:
        await message.reply_text(cached_replies[triggered])
        return

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You're a calm, smart Telegram crypto helper named Chad who speaks like a chill degen and helps the $STUCK community."
                },
                {
                    "role": "user",
                    "content": BASE_PROMPT.format(question=message.text)
                }
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


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_update = update.chat_member
    old_status = member_update.old_chat_member.status
    new_status = member_update.new_chat_member.status

    if old_status == "left" and new_status == "member":
        member = member_update.new_chat_member.user

        if member.is_bot:
            logger.info(f"🤖 Bot joined: {member.username}, ignored.")
            return

        try:
            await context.bot.send_message(
                chat_id=member_update.chat.id,
                text=random.choice([
                    f"📬 Yo *{member.first_name}*, welcome to *$STUCK rehab*. Check your baggage at the door 📉🛐",
                    f"💀 *{member.first_name}* just entered the stuck zone. *No refunds. No roadmap. Just vibes* 🌀",
                    f"🙌 *Welcome {member.first_name}* – your coping journey starts now. *Say gm and hold on tight* 🧠"
                ]),
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)

            await context.bot.send_message(
                chat_id=member_update.chat.id,
                text=f"💊 *Copium Meter* for {member.first_name}: *{random.choice(['💨 Mild Copium', '💊 Medium Dosage', '🔥 Max Cope Mode'])}*",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)

            await context.bot.send_message(
                chat_id=member_update.chat.id,
                text=f"🎖️ *Cope Rank Assigned:* *{random.choice(['Cope Cadet 🍼', 'Stuck Veteran 💀', 'Moon Cultist 🌕', 'Rug Resister 🛡️'])}*",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)

            await context.bot.send_message(
                chat_id=member_update.chat.id,
                text=f"📘 *Did You Know?* {random.choice(['$STUCK only moons when you stop watching the chart 👀📉', 'Shieldy eats bots for breakfast 🍽️🤖', 'We have no utility — just memes and vibes 🧠🚀', 'Chad responds like he’s been rugged 5x this week 😬'])}",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)

            await context.bot.send_message(
                chat_id=member_update.chat.id,
                text="📌 *P.S.* Don’t forget to check the *pinned message* for Moonshot link + group rules!",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.warning(f"Could not welcome user: {e}")


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    logger.info("🚀 StuckSupportBot (a.k.a. Chad) is live and vibin’...")
    await app.run_polling()


if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()

    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
