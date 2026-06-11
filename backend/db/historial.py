from db.client import supabase

def crear_conversacion(user_id: str, titulo: str = "Nueva consulta") -> str:
    """Crea una nueva conversación y retorna su ID"""
    try:
        resultado = supabase.table("conversaciones").insert({
            "user_id": user_id,
            "titulo":  titulo
        }).execute()
        return resultado.data[0]["id"]
    except Exception as e:
        print(f"⚠ Error creando conversación: {e}")
        return None

def guardar_mensaje(conversacion_id: str, rol: str, texto: str):
    """Guarda un mensaje en la conversación"""
    try:
        supabase.table("mensajes").insert({
            "conversacion_id": conversacion_id,
            "rol":             rol,
            "texto":           texto
        }).execute()
    except Exception as e:
        print(f"⚠ Error guardando mensaje: {e}")

def obtener_historial(conversacion_id: str, limite: int = 4) -> list:
    """Obtiene los últimos N mensajes para el contexto de GROQ"""
    try:
        resultado = supabase.table("mensajes")\
            .select("rol, texto")\
            .eq("conversacion_id", conversacion_id)\
            .order("created_at", desc=True)\
            .limit(limite)\
            .execute()

        # Invertir para orden cronológico
        mensajes = resultado.data[::-1]

        return [
            {
                "role":    "user" if m["rol"] == "user" else "assistant",
                "content": m["texto"]
            }
            for m in mensajes
            if m["rol"] in ("user", "bot")
        ]
    except Exception as e:
        print(f"⚠ Error obteniendo historial: {e}")
        return []

def obtener_conversaciones(user_id: str) -> list:
    """Lista todas las conversaciones de un usuario"""
    try:
        resultado = supabase.table("conversaciones")\
            .select("id, titulo, created_at, updated_at")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .execute()
        return resultado.data
    except Exception as e:
        print(f"⚠ Error obteniendo conversaciones: {e}")
        return []

def renombrar_conversacion(conversacion_id: str, nuevo_titulo: str):
    """Renombra una conversación"""
    try:
        supabase.table("conversaciones")\
            .update({"titulo": nuevo_titulo})\
            .eq("id", conversacion_id)\
            .execute()
    except Exception as e:
        print(f"⚠ Error renombrando conversación: {e}")

def eliminar_conversacion(conversacion_id: str):
    """Elimina una conversación y sus mensajes en cascada"""
    try:
        supabase.table("conversaciones")\
            .delete()\
            .eq("id", conversacion_id)\
            .execute()
    except Exception as e:
        print(f"⚠ Error eliminando conversación: {e}")

def actualizar_timestamp(conversacion_id: str):
    """Actualiza updated_at para que aparezca primera en el sidebar"""
    try:
        supabase.table("conversaciones")\
            .update({"updated_at": "now()"})\
            .eq("id", conversacion_id)\
            .execute()
    except Exception as e:
        print(f"⚠ Error actualizando timestamp: {e}")
        
def guardar_resumen(conversacion_id: str, resumen: str):
    """Guarda el resumen de la conversación"""
    try:
        supabase.table("conversaciones")\
            .update({"resumen": resumen})\
            .eq("id", conversacion_id)\
            .execute()
    except Exception as e:
        print(f"⚠ Error guardando resumen: {e}")

def obtener_resumen(conversacion_id: str) -> str:
    """Obtiene el resumen guardado de la conversación"""
    try:
        resultado = supabase.table("conversaciones")\
            .select("resumen")\
            .eq("id", conversacion_id)\
            .execute()

        if resultado.data and resultado.data[0].get("resumen"):
            return resultado.data[0]["resumen"]
        return ""
    except Exception as e:
        print(f"⚠ Error obteniendo resumen: {e}")
        return ""