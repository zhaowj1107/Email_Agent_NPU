from typing import Final
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN:Final= "8025552998:AAFkZrZDYHDICyCycVdXH-34MaoDJAroEp0"
BOT_USERNAME:Final= "@Silviaaaa_bot"

# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm your bot. How can I assist you today?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/custom - Custom command\n"
        "/stop - Stop the bot\n"
    )


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "This is a custom command response!"
    )


# Handle responses

def handle_response(text: str) -> str:
    # Process the text and return a response
    # For now, just echo the received text
    processed: str = text.lower()
    return f"You said: {processed}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"user: {update.message.chat.id} in {message_type} chat: {text}")

    if message_type == "group":
        if BOT_USERNAME in text:
            nex_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = handle_response(text)
        else:
            return
    else:
        response: str = handle_response(text)

    print("bot: ", response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")



if __name__ == "__main__":
    print("Starting bot...")
    # Create the bot application
    app = ApplicationBuilder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))

    # Register message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Register error handler
    app.add_error_handler(error)

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    print("Bot is running...")
    app.run_polling(poll_interval=3)