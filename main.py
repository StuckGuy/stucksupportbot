# main.py (Updated OpenAI client syntax)

import os
import time
import logging
import asyncio
import random
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    ChatMemberHandler,
    Defaults,
)
from openai import OpenAI
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

nest_asyncio.apply()
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_last_message_time = defaultdict(lambda: datetime.min)
RATE_LIMIT_SECONDS = 10
cached_replies = OrderedDict()
MAX_CACHE_SIZE = 50

# ... [rest of constants remain unchanged]

# ✅ Ticker Analyzer
async def handle_ticker_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()
    lowered = text.lower()

    if not any(k in lowered for k in TICKER_KEYWORDS):
        return

    ticker_parts = [word for word in text.split() if word.startswith("$") and len(word) > 1]
    if not ticker_parts:
        return await message.reply_text("Please include a ticker like `$STUCK` to analyze.")

    ticker = ticker_parts[0].upper()

    prompt = f"""
You are a degen crypto analyst who gives brutally honest, meme-style breakdowns of meme coins.
Analyze the token {ticker} and give:
- Pros ✅  
- Cons ❌  
- Vibe check 🙀  
Then give a final rating as one of: WINNER, MID, or STUCK.

Use degen slang, stay brief but spicy. End with:  
"Verdict: STUCK/WINNER/MID"
"""

    await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
    await asyncio.sleep(2)

    try:
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a crypto degen meme expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.9
            )
        )
        reply = response.choices[0].message.content.strip()
        await message.reply_text(reply)

    except asyncio.TimeoutError:
        await message.reply_text("⏱ Chad is still digging through charts… try again soon.")
    except Exception as e:
        logger.exception(f"Error in ticker analyzer: {e}")
        await message.reply_text("Something broke. Probably the chart. Try again later.")

# 🔁 Main Community Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    user_id = message.from_user.id
    now = datetime.now()

    if (now - user_last_message_time[user_id]).total_seconds() < RATE_LIMIT_SECONDS:
        logger.info("⏱️ Rate limit triggered.")
        return
    user_last_message_time[user_id] = now

    text = message.text.lower()

    if any(phrase in text for phrase in SCAM_PHRASES):
        logger.info("⚠️ Scam-like phrase detected, but not deleted.")
        return

    triggered = next((word for word in TRIGGER_CATEGORIES if word in text), None)
    if not triggered:
        logger.info("🔝 No trigger matched for message.")
        return

    logger.info(f"💬 Received message: {message.text} from {message.from_user.username or message.from_user.id}")

    try:
        await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
        await asyncio.sleep(2)
    except:
        pass

    if triggered in cached_replies:
        await message.reply_text(cached_replies[triggered])
        return

    try:
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a calm, smart Telegram crypto helper named Chad who speaks like a chill degen and helps the $STUCK community."},
                    {"role": "user", "content": BASE_PROMPT.format(question=message.text)}
                ],
                max_tokens=160,
                temperature=0.85
            )
        )

        reply = response.choices[0].message.content.strip()
        cached_replies[triggered] = reply

        if len(cached_replies) > MAX_CACHE_SIZE:
            cached_replies.popitem(last=False)

        await message.reply_text(reply)

    except asyncio.TimeoutError:
        logger.warning("🕒 OpenAI timeout.")
        await message.reply_text("Chad’s stuck thinking too hard. Try again in a sec.")
    except Exception as e:
        logger.exception(f"🔥 Full error during OpenAI call or reply: {e}")
        try:
            await message.reply_text("Chad's passed out from too much cope. Try again later.")
        except Exception as reply_fail:
            logger.warning(f"⚠️ Failed to send fallback message: {reply_fail}")

        return

    logger.info(f"💬 Received message: {message.text} from {message.from_user.username or message.from_user.id}")

    try:
        await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
        await asyncio.sleep(2)
    except:
        pass

    if triggered in cached_replies:
        await message.reply_text(cached_replies[triggered])
        return

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You're a calm, smart Telegram crypto helper named Chad who speaks like a chill degen and helps the $STUCK community."},
                        {"role": "user", "content": BASE_PROMPT.format(question=message.text)}
                    ],
                    max_tokens=160,
                    temperature=0.85
                )
            ),
            timeout=10
        )

        reply = response.choices[0].message.content.strip()
        cached_replies[triggered] = reply

        if len(cached_replies) > MAX_CACHE_SIZE:
            cached_replies.popitem(last=False)

        await message.reply_text(reply)

    except asyncio.TimeoutError:
        logger.warning("🕒 OpenAI timeout.")
        await message.reply_text("Chad’s stuck thinking too hard. Try again in a sec.")
    except Exception as e:
        logger.exception(f"🔥 Full error during OpenAI call or reply: {e}")
        try:
            await message.reply_text("Chad's passed out from too much cope. Try again later.")
        except Exception as reply_fail:
            logger.warning(f"⚠️ Failed to send fallback message: {reply_fail}")

# 🫡 Welcome Message
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
                    f"📬 Yo *{member.first_name}*, welcome to *$STUCK rehab*. Check your baggage at the door 📉😐",
                    f"💀 *{member.first_name}* just entered the stuck zone. *No refunds. No roadmap. Just vibes* 🔀",
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
                text=f"🎖️ *Cope Rank Assigned:* *{random.choice(['Cope Cadet 😈', 'Stuck Veteran 💀', 'Moon Cultist 🌕', 'Rug Resister 🛡️'])}*",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)
            await context.bot.send_message(
                chat_id=member_update.chat.id,
                text=f"📘 *Did You Know?* {random.choice(['$STUCK only moons when you stop watching the chart 👀📉', 'Shieldy eats bots for breakfast 🍽️🤖', 'We have no utility — just memes and vibes 😉🚀', 'Chad responds like he’s been rugged 5x this week 😬'])}",
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

# 🧠 Run Bot
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(Defaults(parse_mode="Markdown")).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ticker_analysis))  # Added first
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    logger.info("🚀 StuckSupportBot (a.k.a. Chad) is live and vibin’...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
