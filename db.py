import logging
from own import supabase

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def is_user_allowed(user_id) -> bool:
    response = supabase.table("users").select("user_id").execute()
    allowed = False
    for user in response.data:
        if user['user_id'] == user_id:
            allowed = True
    logging.info(f"User [{user_id}] allowed: {allowed}")
    return allowed

def is_func_open_for_public(func_name) -> bool:
    response = supabase.table("funcs").select("func_name").execute()
    allowed = False
    for func in response.data:
        if func['func_name'] == func_name:
            allowed = True
    logging.info(f"Func [{func_name}] open: {allowed}")
    return allowed

def get_quote() -> tuple[str, str]:
    response = supabase.rpc("get_random_quote").execute()
    data = response.data[0]
    quote, author = data["quote"], data["author"]
    return quote, author

def get_meme() -> tuple[str, str, str]:
    response = supabase.rpc("get_random_meme").execute()
    data = response.data[0]
    path, caption = data["path"], data["caption"]
    ext = str(path).split(".")[1]
    return path, caption, ext

def get_games():
    response = supabase.table("games").select("*").execute()
    return response.data

def insert_meme(path, caption):
    supabase.table("memes").insert({"path": path, "caption": caption}).execute()

def insert_quote(quote, author):
    supabase.table("quotes").insert({"quote": quote, "author": author}).execute()