from PyCharacterAI import get_client
from dotenv import load_dotenv
from utils import Logger, TokenException
from telegram import Update
from utils.decorators import restricted
import os

load_dotenv()

token: str = os.environ.get("CAI_TOKEN")
ai_id: str = os.environ.get("CAI_ID")

if not token or not ai_id:
    raise TokenException("CAI_TOKEN(Character AI) and CAI_ID(Character AI bot ID) are required.")

@restricted
async def say_with_ai(update: Update, prompt: str):

    msg = await update.message.reply_text("Ультра думает над ответом...")

    client = await get_client(token=token)

    chat, start_message = await client.chat.create_chat(ai_id)

    Logger.info(f"AI question from {update.effective_user.full_name} : {prompt}")

    answer = await client.chat.send_message(ai_id, chat.chat_id, prompt)
    
    Logger.info(f"AI answer : {answer.get_primary_candidate().text}")

    await msg.edit_text(answer.get_primary_candidate().text)

    await client.close_session()
