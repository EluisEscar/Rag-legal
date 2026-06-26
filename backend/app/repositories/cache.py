import hashlib
import logging

from app.repositories.client import supabase


logger = logging.getLogger(__name__)


def obtener_cache(pregunta: str) -> str | None:
    """Busca si la pregunta ya fue respondida antes"""
    try:
        resultado = supabase.table("cache_respuestas")\
            .select("respuesta")\
            .eq("pregunta", pregunta.strip().lower())\
            .execute()

        if resultado.data:
            logger.info("Respuesta recuperada del cache exacto")
            return resultado.data[0]["respuesta"]

        return None
    except Exception:
        logger.warning("Error consultando cache exacto", exc_info=True)
        return None

def guardar_cache(pregunta: str, respuesta: str):
    """Guarda una respuesta en caché — ignora si ya existe"""
    try:
        # Verificar si ya existe antes de insertar
        existe = supabase.table("cache_respuestas")\
            .select("id, hits")\
            .eq("pregunta", pregunta.strip().lower())\
            .execute()

        if existe.data:
            # Ya existe — actualizar hits
            supabase.table("cache_respuestas")\
                .update({"hits": existe.data[0].get("hits", 1) + 1})\
                .eq("pregunta", pregunta.strip().lower())\
                .execute()
        else:
            # No existe — insertar
            supabase.table("cache_respuestas").insert({
                "pregunta":  pregunta.strip().lower(),
                "respuesta": respuesta,
                "hits":      1
            }).execute()

    except Exception:
        logger.warning("Error guardando cache exacto", exc_info=True)
        
def generar_clave_cache(
    pregunta: str,
    user_id: str,
    historial: list | None = None,
    modo: str = "rag",
) -> str:
    partes_contexto = [
        mensaje["content"].strip()
        for mensaje in (historial or [])[-4:]
        if mensaje.get("role") == "user" and mensaje.get("content")
    ]
    contexto = " ".join(partes_contexto)[:500]
    contenido = "|".join(
        [
            user_id,
            modo,
            pregunta.strip().lower(),
            contexto,
        ]
    )

    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()
