from telegram import Update
from utils.decorators import restricted
from utils import Logger
import random

@restricted
async def yes_or_no(update: Update):
    # TODO: Перенести варианты ответов в бд?
    yes = bool(random.randint(0, 1))

    yes_answers = ["Да", "Ага", "Думаю да", "Конечно", "Если я скажу да, вы меня отпустите?"]
    no_answer = ["Нет", "Неа", "Думаю нет", "Точно нет"]

    text: str = random.choice(yes_answers) if yes else random.choice(no_answer)

    Logger.info(text)
    
    await update.message.reply_text(text)
