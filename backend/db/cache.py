from db.client import supabase

def obtener_cache(pregunta: str) -> str | None:
    """Busca si la pregunta ya fue respondida antes"""
    try:
        resultado = supabase.table("cache_respuestas")\
            .select("respuesta")\
            .eq("pregunta", pregunta.strip().lower())\
            .execute()

        if resultado.data:
            print(f"✅ Respuesta desde caché — 0 tokens")
            return resultado.data[0]["respuesta"]

        return None
    except Exception as e:
        print(f"⚠ Error en caché: {e}")
        return None

def guardar_cache(pregunta: str, respuesta: str):
    """Guarda una respuesta en caché — ignora si ya existe"""
    try:
        # Verificar si ya existe antes de insertar
        existe = supabase.table("cache_respuestas")\
            .select("id")\
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

    except Exception as e:
        print(f"⚠ Error guardando caché: {e}")