from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, Application
from utils import TokenException
from handlers.start_func import start
from handlers.buttons import button_handler
from handlers.mentions import mention_response
from handlers.add_quote import quote_handler
from handlers.add_meme import meme_handler
from services.ai_answer import ai_manager
import os, asyncio

TOKEN: str = os.environ.get("TG_TOKEN")

if not TOKEN:
    raise TokenException("TG_TOKEN(Telegram bot token) are required.")

class Bot:
    def __init__(self) -> None:
        self.application = (
            ApplicationBuilder()
            .token(TOKEN)
            .post_init(self.on_startup)
            .post_stop(self.on_shutdown)
            .build()
        )

        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(quote_handler)
        self.application.add_handler(meme_handler)
        self.application.add_handler(CallbackQueryHandler(button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT, mention_response))

    async def on_startup(self, app):
        app.create_task(ai_manager.start_session())

    async def on_shutdown(self, app):
        await ai_manager.finish_session()

    def run(self) -> None:
        self.application.run_polling()

if __name__ == "__main__":
    bot = Bot()
    bot.run()