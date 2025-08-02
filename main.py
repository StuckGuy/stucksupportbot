import os
import time
import logging
import asyncio
import random
import nest_asyncio
import requests
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
import openai
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

nest_asyncio.apply()
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_last_message_time = defaultdict(lambda: datetime.min)
RATE_LIMIT_SECONDS = 10
cached_replies = OrderedDict()
MAX_CACHE_SIZE = 50

BUY_TRIGGERS = ["where to buy", "how to buy", "buy stuck", "buy $stuck", "chart", "moonshot", "token", "$stuck", "how do i get", "where can i get", "can i buy", "is it on moonshot"]
DEAD_TRIGGERS = ["dead", "rug", "abandoned", "no team", "still alive", "exit", "pull"]
ROADMAP_TRIGGERS = ["roadmap", "plans", "future", "milestone", "what’s next", "what's next", "what are you building"]
UTILITY_TRIGGERS = ["utility", "use case", "purpose", "what does it do", "what’s the point", "what is stuck for"]
TEAM_TRIGGERS = ["team", "devs", "developers", "who made", "who runs", "who's behind"]
TAX_TRIGGERS = ["tax", "buy tax", "sell tax", "is there a tax"]
WEBSITE_TRIGGERS = ["website", "site", "link", "official page", "where’s the site", "whats the site"]
WEN_MOON_TRIGGERS = ["wen moon", "when moon", "moon", "when lambo", "will it pump"]
GROWTH_TRIGGERS = ["investors", "visibility", "marketing", "reach", "exposure", "community growth", "how to grow", "how can we grow", "get more holders", "get more people"]
SCAM_PHRASES = ["dm", "promo", "partner", "collab", "shill", "call group", "inbox", "promotion", "reach out"]
GENERAL_QUESTIONS = ["what is stuck", "what's this project about", "what is this", "what’s this"]

TRIGGER_CATEGORIES = (
    BUY_TRIGGERS + DEAD_TRIGGERS + ROADMAP_TRIGGERS + UTILITY_TRIGGERS +
    TEAM_TRIGGERS + TAX_TRIGGERS + WEBSITE_TRIGGERS + WEN_MOON_TRIGGERS +
    GROWTH_TRIGGERS + GENERAL_QUESTIONS
)

TICKER_KEYWORDS = ["analyze", "check", "is", "review", "vibe", "opinion", "thoughts"]

BASE_PROMPT = """You're Chad, the chill but knowledgeable $STUCK community helper in Telegram. 
You're still a degen at heart, but you're here to actually help people — not just meme.

Your tone is calm, supportive, and witty. You speak with crypto lingo, but also offer real explanations when needed. 
Be cool, grounded, and don’t yell or act like a clown.

Important context: $STUCK is *first and foremost* a support group to help people grow, learn, and recover from crypto trauma. Memes are the flavor, but growth is the goal.

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

    user_id = message.from_user.id
    now = datetime.now()

    if (now - user_last_message_time[user_id]).total_seconds() < RATE_LIMIT_SECONDS:
        return
    user_last_message_time[user_id] = now

    lowered = message.text.lower()
    if any(word in lowered for word in SCAM_PHRASES):
        try:
            await message.delete()
        except:
            pass
        return

    if lowered in cached_replies:
        await message.reply_text(cached_replies[lowered])
        return

    if not any(trigger in lowered for trigger in TRIGGER_CATEGORIES):
        return

    await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
    await asyncio.sleep(2)

    try:
        prompt = BASE_PROMPT.format(question=message.text.strip())
        response = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a helpful crypto assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.85
            )
        )
        reply = response["choices"][0]["message"]["content"].strip()
        if len(cached_replies) >= MAX_CACHE_SIZE:
            cached_replies.popitem(last=False)
        cached_replies[lowered] = reply
        await message.reply_text(reply)

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await message.reply_text("Chad’s brain is fried. Try again soon.")

async def handle_ticker_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()
    lowered = text.lower()

    if not any(k in lowered for k in TICKER_KEYWORDS):
        return

    words = text.split()
    token_identifier = None

    for word in words:
        if word.startswith("$") and len(word) > 1:
            token_identifier = word[1:]  # Strip dollar sign
            break
        elif len(word) in (44, 45):
            token_identifier = word
            break

    if not token_identifier:
        return await message.reply_text("Please include a token ticker like `$STUCK` or a valid address.")

    headers = {"X-API-KEY": BIRDEYE_API_KEY}

    try:
        if len(token_identifier) in (44, 45):
            token_address = token_identifier
        else:
            search_url = f"https://public-api.birdeye.so/public/search?q={token_identifier}"
            res = requests.get(search_url, headers=headers)
            logger.info(f"Search response: {res.json()}")
            token_address = res.json()["data"][0]["address"]

        logger.info(f"Token address: {token_address}")

        price_url = f"https://public-api.birdeye.so/public/token/{token_address}"
        res = requests.get(price_url, headers=headers)
        logger.info(f"Price response: {res.text}")
        token_data = res.json().get("data", {})

    except Exception as e:
        logger.error(f"Birdeye API error: {e}")
        token_data = {}

    token_info = f"\nReal-Time Stats for {token_identifier}:\n"
    if token_data:
        price = token_data.get('priceUsdt', 0)
        volume = token_data.get('volume24h', 0)
        market_cap = token_data.get('marketCap', 0)

        token_info += f"Price: ${float(price):.6f}\n"
        token_info += f"24h Volume: ${int(volume):,}\n"
        token_info += f"Market Cap: ${int(market_cap):,}\n"
    else:
        token_info += "⚠️ No real data found. Might be new or not on Solana.\n"

    prompt = f"""
You are a degen crypto analyst who gives brutally honest, meme-style breakdowns of meme coins.
Analyze the token {token_identifier} and give:
- Pros ✅  
- Cons ❌  
- Vibe check 🙀  
Then give a final rating as one of: WINNER, MID, or STUCK.

Bonus Tip: If this token had a Tinder bio, drop the funniest one-liner.

Use degen slang, stay brief but spicy. End with:  
"Verdict: STUCK/WINNER/MID"
"""

    await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
    await asyncio.sleep(2)

    try:
        response = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a crypto degen meme expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.9
            )
        )
        reply = response["choices"][0]["message"]["content"].strip()
        await message.reply_text(reply + "\n\n" + token_info)

    except asyncio.TimeoutError:
        await message.reply_text("⏱ Chad is still digging through charts… try again soon.")
    except Exception as e:
        logger.exception(f"Error in ticker analyzer: {e}")
        await message.reply_text("Something broke. Probably the chart. Try again later.")
        return

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(Defaults(parse_mode="Markdown")).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ticker_analysis))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
    logger.info("🚀 StuckSupportBot (a.k.a. Chad) is live and vibin’...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
