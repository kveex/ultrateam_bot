import asyncio
from typing import Optional
from warnings import deprecated

from PyCharacterAI import get_client
from PyCharacterAI.client import AsyncClient
from PyCharacterAI.types import Chat
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
@deprecated("Use send_ai_message() instead")
async def say_with_ai(update: Update, prompt: str):

    msg = await update.message.reply_text("Ультра думает над ответом...")

    client = await get_client(token=token)

    chat, start_message = await client.chat.create_chat(ai_id)

    Logger.info(f"AI question from {update.effective_user.full_name} : {prompt}")

    answer = await client.chat.send_message(ai_id, chat.chat_id, prompt)
    
    Logger.info(f"AI answer : {answer.get_primary_candidate().text}")

    await msg.edit_text(answer.get_primary_candidate().text)

    await client.close_session()

@restricted
async def send_ai_message(update: Update):
    msg = await update.message.reply_text("Ультра думает над ответом...")
    prompt: str = update.message.text

    Logger.info(f"AI question from {update.effective_user.full_name} : {prompt}")

    answer = await ai_manager.get_first_answer(prompt)

    Logger.info(f"AI answer : {answer}")

    await msg.edit_text(answer)

class AIAnswer:
    def __init__(self) -> None:
        self.client: Optional[AsyncClient] = None
        self.chat: Optional[Chat] = None
        self.chat_id: Optional[int] = None

    async def start_session(self) -> None:
        """Создаёт клиент и чат для ИИ чтобы с ним можно было общаться"""
        self.client = await get_client(token=token)
        chat, start_message = await self.client.chat.create_chat(ai_id)
        self.chat = chat
        self.chat_id = chat.chat_id
        Logger.info("AI session started")

    async def get_first_answer(self, prompt: str) -> str:
        """Возвращает первую строку с ответом ИИ"""
        cleared_prompt = " ".join(prompt.lower().replace("ультраии", "").split())
        if not self.client:
            raise RuntimeError("Client not initialized. You should call AIAnswer.start_session() on bot start")
        answer = await self.client.chat.send_message(chat_id=self.chat_id, character_id=ai_id, text=cleared_prompt)
        return answer.get_primary_candidate().text

    async def get_all_answers(self, prompt: str) -> list[str]:
        """Возвращает списов всех строк с ответами ИИ"""
        cleared_prompt = " ".join(prompt.lower().replace("ультраии", "").split())
        if not self.client:
            raise RuntimeError("Client не инициализирован. Возможно стоит вызвать AIAnswer.start_session() при старте бота")
        answer = await self.client.chat.send_message(chat_id=self.chat_id, text=cleared_prompt)
        return answer.get_all_answers()

    async def finish_session(self) -> None:
        """Завершает чат и закрывает клиент ИИ"""
        await self.client.close_session()
        self.client = None
        self.chat = None
        self.chat_id = None
        Logger.info("AI session finished")

ai_manager: AIAnswer = AIAnswer()