from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from utils.decorators import restricted
from utils.database import db
from utils import Logger
import random
from pathlib import Path

FILE, CAPTION, VID_CONFIRM = range(3, 6)

@restricted
async def start_add_meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📩 Пришли видео или фото (как медиа или как файл). "
        "После получения файла я попрошу подпись. Отправьте /cancel чтобы отменить."
    )

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
        ext = Path(filename).suffix
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

    if not Path("memes").exists():
        Path("memes").mkdir()

    filename = f"{random.randint(0, 32000)}_{random.randint(0, 32000)}{ext}"
    out_path = Path("memes") / filename

    try:
        file = await context.bot.get_file(file_id)
        try:
            await file.download_to_drive(out_path)
        except AttributeError:
            await file.download(out_path)
    except Exception as e:
        await query.edit_message_text(f"Ошибка при скачивании файла: {e}")
        return ConversationHandler.END

    try:
        db.upload_meme(out_path, caption)
    except Exception as e:
        await query.edit_message_text(f"Файл сохранён локально как {filename}, но запись в БД упала: {e}")
        context.user_data.pop("file_id", None)
        context.user_data.pop("m_type", None)
        context.user_data.pop("m_ext", None)
        context.user_data.pop("m_caption", None)
        return ConversationHandler.END
    
    try:
        await query.edit_message_text(f"✅ Мем сохранён: {filename}")
    except Exception as e:
        if "Message is not modified" not in str(e):
            raise

    Logger.info(f"Meme saved [{out_path}]")
    context.user_data.pop("file_id", None)
    context.user_data.pop("m_type", None)
    context.user_data.pop("m_ext", None)
    context.user_data.pop("m_caption", None)
    Path(out_path).unlink()
    return ConversationHandler.END


async def cancel_meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление мемa отменено.")
    context.user_data.pop("file_id", None)
    context.user_data.pop("m_type", None)
    context.user_data.pop("m_ext", None)
    m_path = context.user_data.pop("m_path", None)
    if m_path and Path(m_path).exists():
        try:
            Path(m_path).rmdir()
        except Exception:
            pass
    return ConversationHandler.END

meme_handler: ConversationHandler = ConversationHandler(
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