from telegram import Update
import random
from utils import Logger
from utils.decorators import restricted

@restricted
async def pick_who(update: Update):
    #TODO: Перенести варианты ответа в бд?
    names = ["Квикс", "Куст", "Фиш", "Пингвин", "Фелон", "Я"]
    words = ["Думаю", "Наверное", "Вероятно", " ", " ", " "]

    name = random.choice(names)
    word = random.choice(words)
    text = name if word == " " else word + " " + name
    Logger.info(f"Picked person: {name} [{text }]")
    await update.message.reply_text(text)
