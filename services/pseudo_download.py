import asyncio
import random
from telegram import Update
from utils.decorators import restricted

@restricted
async def say_download(update: Update):
    text: str = " ".join(update.message.text.lower().replace("ультраскачай", "").split())
    message = await update.message.reply_text(f"Скачиваю {text}")
    dots_amount = random.randint(3, 10)
    for i in range(1, dots_amount):
        await asyncio.sleep(0.5)
        await message.edit_text(message.text + "." * i)
    else:
        if random.randint(0, 1) == 0:
            await message.edit_text(f"Я не смог скачать {text} :(")
        else:
            await message.edit_text(f"Я скачал {text} :D")