from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_KEY son requeridos")

    return create_client(url, key)

supabase = get_supabase()