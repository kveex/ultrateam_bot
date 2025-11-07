from telegram import Update, MaybeInaccessibleMessage
from telegram.helpers import escape_markdown
from utils.decorators import restricted
from utils.logger import Logger
from utils.database import db

@restricted
async def pick_quote(update: Update, msg: MaybeInaccessibleMessage) -> None:
    quote, author, year = db.get_quote()
    Logger.info(f"Picked Quote by {update.effective_user.full_name}: [{quote}], Author: [{author} {year}]")

    if year is None:
        year = ""

    quote: str = escape_markdown(quote, version=2)
    author: str = escape_markdown(author, version=2)
    year: str = escape_markdown(str(year), version=2)

    text: str = f"_{quote}_\n\n||— *{author} {year}*||"
    await msg.edit_text(text, parse_mode="MarkdownV2")
