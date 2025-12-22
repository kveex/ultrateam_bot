from functools import wraps
from telegram import Update
from utils import Logger
from utils.database import db

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, *args, **kwargs):
        user_id: int = update.effective_user.id
        user_name: str = update.effective_user.full_name
        func_name = func.__name__

        if db.is_user_restricted(user_id, user_name):
            Logger.warn(f"User [{user_name}({user_id})] not allowed to use this bot")
            return None
        
        if db.is_func_restricted(func_name):
            Logger.warn(f"Function [{func_name}] is restricted")
            return None
        
        return await func(update, *args, **kwargs)
    return wrapped