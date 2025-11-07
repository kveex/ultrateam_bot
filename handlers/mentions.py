from telegram import Update
from telegram.ext import ContextTypes
from handlers.start_func import start
from utils.logger import Logger
from utils.decorators import restricted
from utils.database import db
from services.meme import reply_meme
from services.yes_no import yes_or_no
from services.pick_who import pick_who
import re

triggers: list = db.get_triggers()
triggers: list = sorted(triggers, key=lambda x: x["priority"])

def normalize_pattern_from_db(pattern: str) -> str:
    """
    Попытаться привести строку из БД к корректному regex-паттерну.
    - Убирает обёртки вида r'...' или '...' или "..."
    - Если компиляция не проходит, пытается декодировать escape-последовательности
      (в случае двойного экранирования, как '\\)\\s*' в JSON/CSV).
    Возвращает паттерн (возможно исходный) — дальше попробуем скомпилировать.
    """
    if not isinstance(pattern, str):
        return pattern

    p = pattern.strip()

    # Убираем префикс r'...' или r"..." или просто '...'
    if (p.startswith("r'") and p.endswith("'")) or (p.startswith('r"') and p.endswith('"')):
        p = p[2:-1]
    elif (p.startswith("'") and p.endswith("'")) or (p.startswith('"') and p.endswith('"')):
        p = p[1:-1]

    # Попробуем скомпилировать как есть
    try:
        re.compile(p, flags=re.IGNORECASE)
        return p
    except re.error:
        # Если не компилируется, попробуем "раскодировать" эскейпы, которые могли
        # попасть в строку как двойное экранирование (например при сохранении в JSON)
        try:
            p2 = p.encode("utf-8").decode("unicode_escape")
            re.compile(p2, flags=re.IGNORECASE)
            return p2
        except Exception:
            # ничего не помогло — вернём оригинал и позволим логике выше обрабатывать ошибку
            return p

async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text or ""
    text_cf = text.casefold()

    for trigger in triggers:
        trigger_type = trigger.get("trigger_type", "")
        pattern = trigger.get("pattern", "")  # берём прямо из БД

        matched = False

        if trigger_type == "equals":
            if text_cf == (pattern or "").casefold():
                matched = True

        elif trigger_type == "contains":
            if (pattern or "").casefold() in text_cf:
                matched = True

        elif trigger_type == "regex":
            # Нормализуем шаблон и логируем repr для отладки
            norm = normalize_pattern_from_db(pattern)
            Logger.warn(f"Regex trigger raw: {repr(pattern)}, normalized: {repr(norm)}")
            try:
                regex = re.compile(norm, flags=re.IGNORECASE)
                if regex.search(text):
                    matched = True
            except re.error as e:
                # логируем проблему — это ключ к пониманию почему не сработало
                Logger.warning(f"Невалидный regex в триггере: {repr(norm)} — {e}")
                matched = False

        if matched:
            action = trigger.get("action", "")
            Logger.info(f"Mentioned by {update.effective_user.full_name} (pattern: {repr(pattern)}, type: {trigger_type})")
            await run_action(action, update, context)
            return

async def run_action(action, update: Update, context: ContextTypes) -> None:
    if action == "start":
        await start(update, context)
    elif action == "sad":
        await say_funny_stuff(update, ":(")
    elif action == "say_normal":
        await say_funny_stuff(update, "УльтраНормально? Мне было УльтраНормально однажды. Они УльтраЗакрыли меня в УльтраКомнате. УльтраРезиновой УльтраКомнате. УльтраРезиновой УльтраКомнате с УльтраКрысами. И мне было УльтраНормально.")
    elif action == "say_smile":
        await say_funny_stuff(update, ")")
    elif action == "say_heh":
        await say_funny_stuff(update, "Хех...)")
    elif action == "yes_or_no":
        await yes_or_no(update)
    elif action == "pick_who":
        await pick_who(update)
    elif action == "reply_meme":
        await reply_meme(update)
    else:
        Logger.error(f"⚠ unknown action {action}")

@restricted
async def say_funny_stuff(update: Update, text: str):
    await update.message.reply_text(text)
