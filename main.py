import logging
import os
import asyncio
import random
import re
from functools import wraps
from telegram.error import BadRequest
from telegram.helpers import escape_markdown

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, MaybeInaccessibleMessage
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
import db as db
from own import TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

chicken_jockey = [
    "чикен джоке", "чикен жоке", "чикен джоки",
    "чикен жоки", "чикен джокей", "чикен жокей",
    "chicken jockey", "chicken jokey", "chicken jocey"
]

QUOTE, AUTHOR, CONFIRM = range(3)
FILE, CAPTION, VID_CONFIRM = range(3, 6)

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, *args, **kwargs):
        user_id = update.effective_user.id
        func_name = func.__name__
        if not (db.is_user_allowed(user_id) or db.is_func_open_for_public(func_name)):
            logging.warning(f"User [{user_id} not allowed to use this bot or function [{func_name}] is private]")
            return None
        return await func(update, *args, **kwargs)
    return wrapped

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎮 Выбрать игру", callback_data=f"random_game:{user.id}")],
        [InlineKeyboardButton("📜 Случайная цитата", callback_data=f"random_quote:{user.id}")],
        [InlineKeyboardButton("🏳️‍🌈 Случайный мем", callback_data=f"random_meme:{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    name = user.full_name

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет, {name}!\nЧего от меня хочешь?",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    msg = query.message
    requested_function = data[0]
    query_user_id = data[1]

    if int(query_user_id) != query.from_user.id:
        logging.error(f"query id [{query_user_id}] doesn't match with user id [{query.from_user.id}]")
        return None

    match requested_function:
        case "random_game":
            await pick_game(update, msg)
            return None
        case "random_quote":
            await pick_quote(update, msg)
            return None
        case "random_meme":
            await context.bot.delete_message(update.effective_chat.id, msg.message_id)
            await send_meme(update)
            return None
        case "file_cancel":
            await context.bot.send_message(update.effective_chat.id, "Ну лан пока")
            return ConversationHandler.END
    return None

async def pick_game(update: Update, msg: MaybeInaccessibleMessage):
    await msg.edit_text("🎲 Выбираем игру...", reply_markup=None)
    games = db.get_games()
    for _ in range(4):
        await asyncio.sleep(1)
        game = random.choice(games)["name"]
        logging.info(f"Possible game: {game}")
        new_text = f"🎮 Возможно: {game}"
        try:
            await msg.edit_text(new_text)
        except BadRequest as e:
            if "Message is not modified" in e.message:
                continue
            logging.warning(f"Ошибка при редактировании: {e}")
            break

    await asyncio.sleep(1)
    final_game = random.choice(games)["name"]
    logging.info(f"Final game: {final_game}")
    await msg.edit_text(f"✅ Сегодня играем в: *{final_game}*", parse_mode="Markdown")

async def pick_quote(update: Update, msg: MaybeInaccessibleMessage):
    quote, author = db.get_quote()
    text = f"_{escape_markdown(quote, 2)}_\n\n||— *{author}*||"
    await msg.edit_text(text, parse_mode="MarkdownV2")

async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text
    normalno = ["нормально", "н0рмально", "нормальн0", "норм", "нoрм", "Нoрмально"]
    mentions = ["ультра", "хей ультра", "хей, ультра", "ультра!", "привет, ультра", "привет ультра", "придурок", "придурок!", "UltraTeam Botik"]
    funny = re.compile(r'\b[хепи]{2,}\b', re.IGNORECASE)

    if any(mention == text.lower() for mention in mentions):
        await start(update, context)
    elif any(word in text.lower() for word in normalno):
        await say_funny_stuff(update, f"УльтраНормально? Мне было УльтраНормально однажды. Они УльтраЗакрыли меня в УльтраКомнате. УльтраРезиновой УльтраКомнате. УльтраРезиновой УльтраКомнате с УльтраКрысами. И мне было УльтраНормально.")
    elif ")" in text.lower() and "(" not in text.lower():
        await say_funny_stuff(update, ")")
    elif funny.search(text.lower()):
        await say_funny_stuff(update, "Хех...)")
    elif "ультрамнение" in text.lower():
        await yes_or_no(update)
    elif "ультракто" in text.lower():
        await pick_who(update)
    elif any(cj in text.lower() for cj in chicken_jockey):
        await reply_meme(update)
    elif "а тебя никто не спрашивал" == text.lower():
        await say_funny_stuff(update, ":(")

@restricted
async def say_funny_stuff(update: Update, text: str):
    await update.message.reply_text(text)

@restricted
async def remove_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text="⌨️ Клавиатура убрана",
        reply_markup=ReplyKeyboardRemove()
    )

@restricted
async def reply_meme(update: Update):
    path, caption, ext = db.get_meme()
    logging.info(path)
    logging.info(ext)
    if ext == "mp4":
        await update.message.reply_video(video=path, caption=caption)
    elif ext == "jpg":
        await update.message.reply_photo(path, caption)

async def send_meme(update: Update):
    path, caption, ext = db.get_meme()
    logging.info(ext)
    if ext == "mp4":
        await update.effective_chat.send_video(video=path, caption=caption)
    elif ext == "jpg":
        await update.effective_chat.send_photo(path, caption)

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
        db.insert_quote(quote, author)

        await query.edit_message_text("✅ Цитата сохранена!")
    else:
        await query.edit_message_text("❌ Добавление цитаты отменено.")

    return ConversationHandler.END

@restricted
async def start_add_meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📩 Пришлите видео или фото (как медиа или как файл). "
        "После получения файла я попрошу подпись. Отправьте /cancel чтобы отменить."
    )
    # очистим прошлые данные на случай
    context.user_data.pop("m_path", None)
    context.user_data.pop("m_temp_downloaded", None)
    context.user_data.pop("file_id", None)
    context.user_data.pop("m_type", None)
    context.user_data.pop("m_caption", None)
    return FILE


async def file_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        await update.message.reply_text("Не получилось получить сообщение. Повторите, пожалуйста.")
        return FILE

    if msg.video:
        file_id = msg.video.file_id
        media_type = "video"
        ext = ".mp4"
    elif msg.photo:
        largest = msg.photo[-1]
        file_id = largest.file_id
        media_type = "photo"
        ext = ".jpg"
    elif msg.document:
        file_id = msg.document.file_id
        filename = getattr(msg.document, "file_name", "") or ""
        ext = os.path.splitext(filename)[1] or ""
        mime = getattr(msg.document, "mime_type", "") or ""
        if mime.startswith("video") and not ext:
            ext = ".mp4"
        media_type = "video" if mime.startswith("video") else "document"
        if not ext:
            ext = ".dat"
    else:
        await msg.reply_text(
            "🥺 Пожалуйста пришлите видео или фото (как файл/медиа).",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data=f"file_cancel:{msg.from_user.id}")]]
            )
        )
        return FILE

    context.user_data["file_id"] = file_id
    context.user_data["m_type"] = media_type
    context.user_data["m_ext"] = ext

    await update.message.reply_text("Файл получен. Отправьте подпись к файлу (или /skip чтобы пропустить).")
    return CAPTION


async def caption_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.text or ""
    context.user_data["m_caption"] = caption

    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="meme_confirm:confirm"),
            InlineKeyboardButton("❌ Отменить", callback_data="meme_confirm:cancel"),
        ]
    ]
    await update.message.reply_text("Вроде смешняво. Добавляем?", reply_markup=InlineKeyboardMarkup(keyboard))
    return VID_CONFIRM


async def skip_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["m_caption"] = ""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="meme_confirm:confirm"),
            InlineKeyboardButton("❌ Отменить", callback_data="meme_confirm:cancel"),
        ]
    ]
    await update.message.reply_text("Без подписи. Добавляем?", reply_markup=InlineKeyboardMarkup(keyboard))
    return VID_CONFIRM


async def file_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = (query.data or "")
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "cancel":
        context.user_data.pop("file_id", None)
        context.user_data.pop("m_type", None)
        context.user_data.pop("m_ext", None)
        context.user_data.pop("m_caption", None)
        await query.edit_message_text("Добавление отменено.")
        return ConversationHandler.END

    file_id = context.user_data.get("file_id")
    media_type = context.user_data.get("m_type")
    ext = context.user_data.get("m_ext", "")
    caption = context.user_data.get("m_caption", "")

    if not file_id or not media_type:
        await query.edit_message_text("Что-то пошло не так — нет данных о файле. Отмена.")
        return ConversationHandler.END

    if not ext:
        ext = ".dat"
    filename = f"{random.randint(0, 32000)}_{random.randint(0, 32000)}{ext}"
    out_path = os.path.join("memes", filename)

    try:
        file = await context.bot.get_file(file_id)
        try:
            await file.download_to_drive(out_path)
        except AttributeError:
            # fallback для старых версий PTB
            await file.download(out_path)
    except Exception as e:
        await query.edit_message_text(f"Ошибка при скачивании файла: {e}")
        return ConversationHandler.END

    try:
        db.insert_meme(out_path, caption)
    except Exception as e:
        await query.edit_message_text(f"Файл сохранён локально как {filename}, но запись в БД упала: {e}")
        context.user_data.pop("file_id", None)
        context.user_data.pop("m_type", None)
        context.user_data.pop("m_ext", None)
        context.user_data.pop("m_caption", None)
        return ConversationHandler.END

    await query.edit_message_text(f"Сохранено: {filename}")
    context.user_data.pop("file_id", None)
    context.user_data.pop("m_type", None)
    context.user_data.pop("m_ext", None)
    context.user_data.pop("m_caption", None)
    return ConversationHandler.END


async def cancel_meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление мемa отменено.")
    context.user_data.pop("file_id", None)
    context.user_data.pop("m_type", None)
    context.user_data.pop("m_ext", None)
    m_path = context.user_data.pop("m_path", None)
    if m_path and os.path.exists(m_path):
        try:
            os.remove(m_path)
        except Exception:
            pass
    return ConversationHandler.END


@restricted
async def yes_or_no(update: Update):

    yes = bool(random.randint(0, 1))

    yes_answers = ["Да", "Ага", "Думаю да", "Конечно", "Если я скажу да, вы меня отпустите?"]
    no_answer = ["Нет", "Неа", "Думаю нет", "Точно нет"]

    text = random.choice(yes_answers) if yes else random.choice(no_answer)
    await update.message.reply_text(text)

@restricted
async def pick_who(update: Update):
    names = ["Квикс", "Куст", "Фиш", "Пингвин", "Я"]
    words = ["Думаю", "Наверное", "Вероятно", " ", " ", " "]

    name = random.choice(names)
    word = random.choice(words)
    text = name if word == " " else word + " " + name
    logging.info(f"Picked person: {name} [{text }]")
    await update.message.reply_text(text)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    quote_handler = ConversationHandler(
        entry_points=[CommandHandler("add_quote", start_add_quote)],
        states={
            QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quote_received)],
            AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, author_received)],
            CONFIRM: [CallbackQueryHandler(confirm_or_cancel, pattern="^(confirm|cancel)$")]
        },
        fallbacks=[],
        per_message=False
    )
    meme_handler = ConversationHandler(
    entry_points=[CommandHandler("add_meme", start_add_meme)],
    states={
        FILE: [
            MessageHandler(filters.VIDEO | filters.PHOTO | filters.Document.ALL, file_received),
            MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("Пожалуйста, пришлите файл (видео или фото).") or FILE),
        ],
        CAPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, caption_received),
            CommandHandler("skip", skip_caption),
        ],
        VID_CONFIRM: [
            CallbackQueryHandler(file_confirmed, pattern=r"^meme_confirm:(confirm|cancel)$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_meme)],
    per_message=False,
)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(quote_handler)
    application.add_handler(meme_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler('remove_this_fucking_keyboard', remove_buttons))
    application.add_handler(MessageHandler(filters.TEXT, mention_response))


    logging.info("Бот запущен")
    application.run_polling()
