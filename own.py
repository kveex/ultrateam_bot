from supabase import create_client, Client
import os
TOKEN = os.environ.get("TOKEN")
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)