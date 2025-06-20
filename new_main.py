import logging
import asyncio
import random
from functools import wraps
from telegram.error import BadRequest

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import db
from own import TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Список игр
GAMES = [
    "Bopl Battle", "Buckshot Roulette", "Content Warning",
    "Lethal Company", "R.E.P.O", "WEBFISHING",
    "Minecraft", "Roblox", "Deep Rock Galactic"
]
QUOTE, AUTHOR, CONFIRM = range(3)

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not db.is_allowed(uid):
            return None
        return await func(update, context)
    return wrapped


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 Выбрать игру", callback_data="random_game")],
        [InlineKeyboardButton("📜 Случайная цитата", callback_data="random_quote")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    name = update.effective_user.full_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет, {name}!\nЧего от меня хочешь?",
        reply_markup=reply_markup
    )

@restricted
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    msg = query.message

    if data == "random_game":

        await msg.edit_text("🎲 Выбираем игру...", reply_markup=None)
        for _ in range(6):
            await asyncio.sleep(1)
            game = random.choice(GAMES)
            new_text = f"🎮 Возможно: {game}"
            try:
                await msg.edit_text(new_text)
            except BadRequest as e:
                if "Message is not modified" in e.message:
                    continue
                logging.warning(f"Ошибка при редактировании: {e}")
                break

        await asyncio.sleep(1)
        final_game = random.choice(GAMES)
        await msg.edit_text(f"✅ Сегодня играем в: *{final_game}*", parse_mode="Markdown")

    elif data == "random_quote":
        quote, author = db.get_quote()
        text = f"_{quote}_\n\n— *{author}*"
        await msg.edit_text(text, parse_mode="Markdown")

@restricted
async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text
    normalno = ["нормально", "н0рмально", "нормальн0", "норм", "нoрм", "Нoрмально"]
    mentions = ["ультра", "хей ультра", "хей, ультра", "ультра!", "привет, ультра", "привет ультра", "придурок", "придурок!", "UltraTeam Botik"]
    chicken_jockey = ["чикен джоке", "чикен жоке", "чикен джоки", "чикен жоки", "чикен джокей", "чикен жокей", "chicken jockey", "chicken jokey", "chicken jocey"]
    if any(mention == text.lower() for mention in mentions):
        await start(update, context)
    elif any(word in text.lower() for word in normalno):
        await message.reply_text(f"УльтраНормально? Мне было УльтраНормально однажды. Они УльтраЗакрыли меня в УльтраКомнате. УльтраРезиновой УльтраКомнате. УльтраРезиновой УльтраКомнате с УльтраКрысами. И мне было УльтраНормально.")
    elif ")" in text.lower() and "(" not in text.lower():
        await message.reply_text(")")
    elif "ультрамнение" in text.lower():
        await message.reply_text(yes_or_no())
    elif "ультракто" in text.lower():
        await message.reply_text(pick_who())
    elif any(cj in text.lower() for cj in chicken_jockey):
        await message.reply_video("cj.mp4")

@restricted
async def remove_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text="⌨️ Клавиатура убрана",
        reply_markup=ReplyKeyboardRemove()
    )

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
        quote = context.user_data["quote"]
        author = context.user_data["author"]

        # 💾 Сюда вставьте свою запись в БД:
        db.cursor.execute("INSERT INTO quotes (quote, author) VALUES (?, ?)", (quote, author))
        db.connection.commit()  # если у вас подключение называется иначе — поправьте

        await query.edit_message_text("✅ Цитата сохранена!")
    else:
        await query.edit_message_text("❌ Добавление цитаты отменено.")

    return ConversationHandler.END

def yes_or_no() -> str:

    yes = bool(random.randint(0, 1))

    yes_answers = ["Да", "Ага", "Думаю да", "Конечно"]
    no_answer = ["Нет", "Неа", "Думаю нет", "Точно нет"]

    text = random.choice(yes_answers) if yes else random.choice(no_answer)
    return text

def pick_who() -> str:
    names = ["Квикс", "Куст", "Фиш", "Пингвин", "Я"]
    words = ["Думаю", "Наверное", "Вероятно", "", "", ""]

    name = random.choice(names)
    word = random.choice(words)
    if word == "":
        return name
    else:
        return word + " " + name

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_quote", start_add_quote)],
        states={
            QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_received)],
            AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, author_received)],
            CONFIRM: [CallbackQueryHandler(confirm_or_cancel, pattern="^(confirm|cancel)$")]
        },
        fallbacks=[],
        per_message=False
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler('remove_this_fucking_keyboard', remove_buttons))
    application.add_handler(MessageHandler(filters.TEXT, mention_response))


    logging.info("Бот запущен")
    application.run_polling()
