from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
from handlers.start_func import start
from handlers.buttons import button_handler
from handlers.mentions import mention_response
from handlers.add_quote import quote_handler
from handlers.add_meme import meme_handler
import os

TOKEN: str = os.environ.get("TOKEN")

class Bot():
    def __init__(self) -> None:
        self.application= ApplicationBuilder().token(TOKEN).build()

        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(quote_handler)
        self.application.add_handler(meme_handler)
        self.application.add_handler(CallbackQueryHandler(button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT, mention_response))

    def run(self) -> None:
        self.application.run_polling()

if __name__ == "__main__":
    bot = Bot()
    bot.run()