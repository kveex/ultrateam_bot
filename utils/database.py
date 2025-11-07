from supabase import create_client, Client
from dotenv import load_dotenv
from utils.logger import Logger
import os

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

class Database:
    def __init__(self, client: Client) -> None:
        self.db: Client = client

    def is_user_restricted(self, user_id: int, user_name: str) -> bool:
        restricted: bool = False
        responce = self.db.table("users").select("user_restricted").eq("user_id", user_id).limit(1).execute()
        if not responce.data:
            self.db.table("users").insert({"user_id": user_id, "user_name": user_name, "user_restricted": False}).execute()
            Logger.info(f"New user added [{user_name}({user_id})]")
            return restricted
        
        restricted = responce.data[0]["user_restricted"]
        return restricted
    
    def is_func_restricted(self, func_name: str) -> bool:
        restricted: bool = False
        responce = self.db.table("funcs").select("func_restricted").eq("func_name", func_name).limit(1).execute()
        if not responce.data:
            self.db.table("funcs").insert({"func_name": func_name, "func_restricted": True}).execute()
            Logger.info(f"New function added [{func_name}]")
            return restricted
        
        restricted = responce.data[0]["func_restricted"]
        return restricted
    
    def get_quote(self) -> tuple[str, str, int]:
        response = self.db.rpc("get_random_quote").execute()

        data = response.data[0]
        quote: str = data["quote"]
        author: str = data["author"]
        year: int = data["year"]

        return quote, author, year
    
    def insert_quote(self, quote: str, author: str, year: int) -> None:
        self.db.table("quotes").insert({"quote": quote, "author": author, "year": year}).execute()

    def get_meme(self) -> tuple[str, str, str]:
        response = self.db.rpc("get_random_meme").execute()
        data = response.data[0]
        path: str = data["path"]
        caption: str = data["caption"]
        ext: str = path.split(".")[1]
        return path, caption, ext

    def get_games(self):
        response = self.db.table("games").select("*").execute()
        return response.data

    def insert_meme(self, path: str, caption: str) -> None:
        self.db.table("memes").insert({"path": path, "caption": caption}).execute()

    def get_triggers(self):
        response = self.db.table("triggers").select("*").execute()
        return response.data
    
    def fix_memes(self):
        response = self.db.table("memes").select("path").execute()
        memes: list = response.data

        good_status: bool = True

        for meme in memes:
            if not os.path.exists(meme["path"]):
                good_status = False
                Logger.warn(f"Found broken path [{meme["path"]}]")
                self.db.table("memes").delete().eq("path", meme["path"]).execute()

        if good_status:
            Logger.info("Database cleaned")

db: Database = Database(create_client(url, key))