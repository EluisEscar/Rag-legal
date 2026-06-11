from db.client import supabase
from sentence_transformers import SentenceTransformer
import numpy as np

# Usa el mismo modelo que los embeddings del RAG
_modelo = None

def get_modelo():
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer(
            'paraphrase-multilingual-mpnet-base-v2'
        )
    return _modelo

def similitud_coseno(v1: list, v2: list) -> float:
    """Calcula similitud coseno entre dos vectores"""
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def buscar_cache_semantico(
    pregunta: str,
    threshold: float = 0.85
) -> str | None:
    try:
        modelo = get_modelo()
        vector_pregunta = modelo.encode(pregunta).tolist()

        resultado = supabase.table("cache_semantico")\
            .select("id, pregunta, respuesta")\
            .execute()

        print(f"🔍 Caché semántico: {len(resultado.data)} entradas")

        if not resultado.data:
            return None

        mejor_score     = 0
        mejor_respuesta = None
        mejor_id        = None

        for item in resultado.data:
            vector_cached = modelo.encode(item["pregunta"]).tolist()
            score = similitud_coseno(vector_pregunta, vector_cached)
            print(f"🔍 Score con '{item['pregunta'][:40]}': {score:.3f}")

            if score > mejor_score:
                mejor_score     = score
                mejor_respuesta = item["respuesta"]
                mejor_id        = item["id"]

        print(f"🔍 Mejor score: {mejor_score:.3f} — threshold: {threshold}")

        if mejor_score >= threshold:
            print(f"✅ Caché semántico hit — similitud: {mejor_score:.3f}")
            return mejor_respuesta

        return None

    except Exception as e:
        print(f"⚠ Error en caché semántico: {e}")
        return None

def guardar_cache_semantico(pregunta: str, respuesta: str):
    try:
        print(f"💾 Guardando en caché semántico: '{pregunta[:50]}'")
        supabase.table("cache_semantico").insert({
            "pregunta":  pregunta,
            "respuesta": respuesta,
            "hits":      1
        }).execute()
        print(f"✅ Guardado en caché semántico")
    except Exception as e:
        print(f"⚠ Error guardando caché semántico: {e}")