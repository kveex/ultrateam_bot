from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.decorators import restricted

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎮 Выбрать игру", callback_data=f"random_game:{user.id}")],
        [InlineKeyboardButton("📜 Случайная цитата", callback_data=f"random_quote:{user.id}")],
        [InlineKeyboardButton("🏳️‍🌈 Случайный мем", callback_data=f"random_meme:{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    name: str = user.full_name

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет, {name}!\nЧего от меня хочешь?",
        reply_markup=reply_markup
    )
