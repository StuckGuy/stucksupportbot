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

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to StuckBot 🤖 — type anything and I’ll roast or help you!")

# Main message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await update.message.chat.send_action(action="typing")

    try:
        response = await asyncio.to_thread(generate_response, user_input)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("😵 Chad is stuck. Try again later.")

# OpenAI reply generator
def generate_response(prompt: str) -> str:
    result = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You're Chad, a sarcastic Telegram crypto degen who helps meme coin holders cope and laugh while answering questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.75,
        max_tokens=150,
    )
    return result.choices[0].message["content"]

# Launch bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 StuckBot is live.")
    app.run_polling()
