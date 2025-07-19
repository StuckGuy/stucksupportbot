import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import openai

# Logging for debugging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Define basic start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! I'm StuckBot — ask me anything!")

# Handle general messages with GPT-4
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Optional: Trigger filtering (example)
    if "moonshot" in user_message.lower():
        await update.message.reply_text("🚀 Want to ape early? Try Moonshot: https://moonshot.com?ref=Xonkwkbt80")
        return

    try:
        response = await asyncio.to_thread(get_openai_reply, user_message)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        await update.message.reply_text("😅 Sorry, I got stuck for a second. Try again!")

# OpenAI response function (sync for background use)
def get_openai_reply(prompt):
    chat_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a sarcastic, meme-style crypto support bot named StuckBot. Keep replies short, funny, and helpful. Never DM users. Only use public replies.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=150,
    )
    return chat_completion.choices[0].message["content"]

# Main app
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 StuckBot is running...")
    app.run_polling()
