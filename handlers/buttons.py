from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.logger import Logger
from services.game import pick_game
from services.quote import pick_quote
from services.meme import send_meme

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    msg = query.message
    requested_function = data[0]
    query_user_id = data[1]

    if int(query_user_id) != query.from_user.id:
        Logger.error(f"query id [{query_user_id}] doesn't match with user id [{query.from_user.id}]")
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
