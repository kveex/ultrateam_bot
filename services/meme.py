from telegram import Update
from utils.decorators import restricted
from utils import Logger
from utils.database import db

@restricted
async def reply_meme(update: Update):
    path, caption, ext = db.get_meme()
    Logger.info(f"Replying meme:\nFile: [{path}]\nCaption: [{caption}]")
    if ext == ".mp4":
        await update.message.reply_video(video=path, caption=caption)
    elif ext == ".jpg":
        await update.message.reply_photo(path, caption)

@restricted
async def send_meme(update: Update):
    path, caption, ext = db.get_meme()
    Logger.info(f"Sending meme:\nFile: [{path}]\nCaption: [{caption}]")
    if ext == ".mp4":
        await update.effective_chat.send_video(video=path, caption=caption)
    elif ext == ".jpg":
        await update.effective_chat.send_photo(photo=path, caption=caption)
