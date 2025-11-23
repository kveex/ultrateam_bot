from telegram import Update
from telegram.ext import ContextTypes
from handlers.start_func import start
from utils import Logger
from utils.decorators import restricted
from utils.database import db
from services.meme import reply_meme
from services.yes_no import yes_or_no
from services.pick_who import pick_who
from services.ai_answer import say_with_ai
import re

async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text or ""
    text_cf = text.casefold()

    triggers: list = sorted(db.get_triggers(), key=lambda x: x["priority"])

    for trigger in triggers:
        trigger_type = trigger["trigger_type"]
        pattern = trigger["pattern"]
        action = trigger["action"]

        matched = False

        if trigger_type == "equals":
            if text_cf == (pattern or "").casefold():
                matched = True

        elif trigger_type == "contains":
            if (pattern or "").casefold() in text_cf:
                matched = True

        elif trigger_type == "hard":
            Logger.info(f"Mentioned by {update.effective_user.full_name} (pattern: {repr(pattern)}, type: {trigger_type}, action: {action})")
            await run_hard_action(update)
            return

        if matched:
            Logger.info(f"Mentioned by {update.effective_user.full_name} (pattern: {repr(pattern)}, type: {trigger_type}, action: {action})")
            await run_action(action, update, context)
            return

async def run_action(action: str, update: Update, context: ContextTypes) -> None:
    if action == "start":
        await start(update, context)
    elif action == "sad":
        await say_funny_stuff(update, ":(")
    elif action == "say_normal":
        await say_funny_stuff(update, "УльтраНормально? Мне было УльтраНормально однажды. Они УльтраЗакрыли меня в УльтраКомнате. УльтраРезиновой УльтраКомнате. УльтраРезиновой УльтраКомнате с УльтраКрысами. И мне было УльтраНормально.")
    elif action == "yes_or_no":
        await yes_or_no(update)
    elif action == "pick_who":
        await pick_who(update)
    elif action == "reply_meme":
        await reply_meme(update)
    elif action == "ai_answer":
        await say_with_ai(update, update.message.text.casefold())
    else:
        Logger.error(f"⚠ unknown action {action}")

async def run_hard_action(update: Update):
    funny = re.compile(r'\b[хепи]{2,}\b', re.IGNORECASE)
    text = update.message.text.casefold()
    if ")" in text.lower() and "(" not in text.lower():
        await say_funny_stuff(update, ")")
    elif funny.search(text.lower()):
        await say_funny_stuff(update, "Хех...)")

@restricted
async def say_funny_stuff(update: Update, text: str):
    await update.message.reply_text(text)
