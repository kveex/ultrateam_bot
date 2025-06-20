import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
connection = sqlite3.connect("bot.db")
cursor = connection.cursor()

try:
    cursor.execute("CREATE TABLE users(user_id INT UNIQUE, can_use BOOL DEFAULT false)")
except sqlite3.OperationalError:
    pass

def is_allowed(user_id) -> bool:
    data = cursor.execute("SELECT can_use FROM users WHERE user_id = ?", (user_id,))
    res = data.fetchone()
    # logging.info(res)
    try:
        allowed = bool(res[0])
    except TypeError:
        allowed = False
    logging.info(f"Is [{user_id}] allowed: {allowed}")
    return allowed

def get_quote() -> tuple[str, str]:
    cursor.execute("SELECT quote, author FROM quotes ORDER BY RANDOM() LIMIT 1")
    quote, author = cursor.fetchone()
    return quote, author