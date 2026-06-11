from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
import os

load_dotenv()

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_KEY son requeridos")

    return create_client(url, key)

supabase = get_supabase()

def generar_clave_cache(pregunta: str, historial: list = None) -> str:
    if not historial:
        return pregunta.strip().lower()

    contexto = " ".join([
        msg["content"] for msg in historial[-4:]
        if msg["role"] == "user"
    ])

    if len(contexto.split()) < 5:
        return pregunta.strip().lower()

    texto = f"{pregunta.strip().lower()}|{contexto[:200]}"
    return hashlib.md5(texto.encode()).hexdigest()