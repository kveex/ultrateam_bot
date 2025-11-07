from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from utils.decorators import restricted
from utils.database import db
from utils.logger import Logger
import datetime

QUOTE, AUTHOR, CONFIRM = range(3)

@restricted
async def start_add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍ Напиши цитату:")
    return QUOTE

# Получили цитату
async def quote_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quote"] = update.message.text
    await update.message.reply_text("👤 Теперь укажи автора:")
    return AUTHOR

# Получили автора — спрашиваем подтверждение
async def author_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["author"] = update.message.text
    quote = context.user_data["quote"]
    author = context.user_data["author"]

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
         InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    text = f"📋 Проверь:\n\n{quote}\n\n  — {author}\n\nСохранить?"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

# Подтверждение или отмена
@restricted
async def confirm_or_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm":
        quote: str = context.user_data["quote"]
        author: str = context.user_data["author"]
        year: int = datetime.datetime.now().year

        clean_author: str = " ".join(word for word in author.split() if word != str(year))

        Logger.info(f"Adding quote: [{quote}], Author: [{clean_author} {year}]")

        db.insert_quote(quote, clean_author, year)

        await query.edit_message_text("✅ Цитата сохранена!")
    else:
        await query.edit_message_text("❌ Добавление цитаты отменено.")

    return ConversationHandler.END

quote_handler: ConversationHandler = ConversationHandler(
            entry_points=[CommandHandler("add_quote", start_add_quote)],
            states={
                QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_received)],
                AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, author_received)],
                CONFIRM: [CallbackQueryHandler(confirm_or_cancel, pattern="^(confirm|cancel)$")]
            },
            fallbacks=[],
            per_message=False
        )
