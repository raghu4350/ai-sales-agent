"""
telegram_bot.py

Runs the AI Sales Agent as a Telegram Bot.
Anyone with Telegram can chat with the agent.

Setup:
1. Open Telegram → search @BotFather
2. Send /newbot → give it a name
3. Copy the token into .env as TELEGRAM_BOT_TOKEN
4. Run: python telegram_bot.py

How it works:
- User sends a message to the bot on Telegram
- Bot passes it to agent.py (using Telegram chat_id as session key)
- agent.py replies using Groq LLM + RAG
- When user says bye/thank you → lead saved to SQLite + email sent

No ngrok needed. No Twilio needed. Works for anyone on Telegram. Free.
"""

import os
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from agent import get_agent_response, is_end_of_call, finalize_lead, clear_call_memory

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing from .env. Get it from @BotFather on Telegram.")

# Set up logging so you can see activity in the terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# /start command
# Shown when user first opens the bot
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)
    first_name = update.effective_chat.first_name or "there"

    # Clear any old memory for this user (fresh start)
    clear_call_memory(chat_id)

    greeting = (
        f"👋 Hello {first_name}! I am an AI Sales Assistant.\n\n"
        f"Tell me what product or service you are looking for "
        f"and I will help qualify your needs.\n\n"
        f"Type /end at any time to finish the conversation and save your details."
    )

    await update.message.reply_text(greeting)
    logger.info(f"New session started for chat_id: {chat_id}")


# --------------------------------------------------
# /end command
# User can manually end the conversation
# --------------------------------------------------

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)

    await update.message.reply_text(
        "✅ Thank you for speaking with us! Let me save your details..."
    )

    await _finalize_session(chat_id, update)


# --------------------------------------------------
# Handle every normal text message
# --------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id    = str(update.effective_chat.id)
    user_text  = update.message.text.strip()

    logger.info(f"[{chat_id}] User: {user_text}")

    # Check if this is an end-of-conversation message
    if is_end_of_call(user_text):

        # Give a natural closing reply first
        await update.message.reply_text(
            "Thank you for speaking with us! Let me save your details..."
        )
        await _finalize_session(chat_id, update)
        return

    # Normal conversation turn — get agent reply
    reply = get_agent_response(chat_id, user_text)

    logger.info(f"[{chat_id}] Agent: {reply}")
    await update.message.reply_text(reply)


# --------------------------------------------------
# Finalize lead: extract → score → save → email
# --------------------------------------------------

async def _finalize_session(chat_id: str, update: Update):

    try:
        finalize_lead(chat_id)
        clear_call_memory(chat_id)

        await update.message.reply_text(
            "✅ Your details have been saved successfully!\n\n"
            "📧 A summary has been sent to your email (if you provided one).\n\n"
            "Our team will get back to you shortly. "
            "Send /start to begin a new conversation anytime."
        )

    except Exception as e:
        logger.error(f"Error finalizing lead for {chat_id}: {e}")
        await update.message.reply_text(
            "✅ Thank you! Your conversation has been recorded.\n"
            "Send /start to begin a new conversation."
        )
        clear_call_memory(chat_id)


# --------------------------------------------------
# Main — Start the bot
# --------------------------------------------------

def main():

    print("=" * 50)
    print("  AI SALES AGENT — TELEGRAM BOT")
    print("  Bot is running. Press Ctrl+C to stop.")
    print("=" * 50)

    from telegram.request import HTTPXRequest

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end",   end))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling (no ngrok needed — bot polls Telegram servers)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
