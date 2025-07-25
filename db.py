import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
connection = sqlite3.connect("bot.db")
cursor = connection.cursor()

def is_user_allowed(user_id) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id, ))
    allowed = cursor.fetchone() is not None
    logging.info(f"User [{user_id}] allowed: {allowed}")
    return allowed

def is_func_open_for_public(func_name) -> bool:
    cursor.execute("SELECT 1 FROM funcs WHERE func_name = ?", (func_name, ))
    allowed = cursor.fetchone() is not None
    logging.info(f"Func [{func_name}] open: {allowed}")
    return allowed

def get_quote() -> tuple[str, str]:
    cursor.execute("SELECT quote, author FROM quotes ORDER BY RANDOM() LIMIT 1")
    quote, author = cursor.fetchone()
    return quote, author

def get_meme() -> tuple[str, str]:
    cursor.execute("SELECT path, caption FROM memes ORDER BY RANDOM() LIMIT 1")
    path, caption = cursor.fetchone()
    return path, caption