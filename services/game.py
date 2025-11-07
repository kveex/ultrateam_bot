from telegram import Update, MaybeInaccessibleMessage
from telegram.error import BadRequest
import asyncio
import random
from utils.decorators import restricted
from utils.logger import Logger
from utils.database import db

@restricted
async def pick_game(update: Update, msg: MaybeInaccessibleMessage):
    await msg.edit_text("🎲 Выбираем игру...", reply_markup=None)
    games = db.get_games()
    for _ in range(4):
        await asyncio.sleep(1)
        game: str = random.choice(games)["name"]
        Logger.info(f"Possible game: {game}")
        new_text: str = f"🎮 Возможно: {game}"
        try:
            await msg.edit_text(new_text)
        except BadRequest as e:
            if "Message is not modified" in e.message:
                continue
            Logger.warning(f"Ошибка при редактировании: {e}")
            break

    await asyncio.sleep(1)
    final_game: str = random.choice(games)["name"]
    Logger.info(f"Final game: {final_game}")
    await msg.edit_text(f"✅ Сегодня играем в: *{final_game}*", parse_mode="Markdown")
