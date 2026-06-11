import logging

import numpy as np

from app.repositories.client import supabase
from app.services.embeddings import EmbeddingPersonalizado


logger = logging.getLogger(__name__)
_embedding_cache: dict[str, tuple[float, ...]] = {}
_MAX_EMBEDDING_CACHE = 2048


def similitud_coseno(v1: list, v2: list) -> float:
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _generar_embedding(
    modelo: EmbeddingPersonalizado,
    texto: str,
) -> tuple[float, ...]:
    if texto not in _embedding_cache:
        if len(_embedding_cache) >= _MAX_EMBEDDING_CACHE:
            _embedding_cache.pop(next(iter(_embedding_cache)))
        _embedding_cache[texto] = tuple(modelo.encode(texto))
    return _embedding_cache[texto]


def _namespace(user_id: str) -> str:
    return f"user:{user_id}|"


def buscar_cache_semantico(
    pregunta: str,
    user_id: str,
    modelo: EmbeddingPersonalizado,
    threshold: float = 0.85,
) -> str | None:
    try:
        vector_pregunta = _generar_embedding(
            modelo,
            pregunta.strip().lower(),
        )
        namespace = _namespace(user_id)
        resultado = (
            supabase.table("cache_semantico")
            .select("id, pregunta, respuesta")
            .like("pregunta", f"{namespace}%")
            .limit(500)
            .execute()
        )

        if not resultado.data:
            return None

        mejor_score = 0.0
        mejor_respuesta = None

        for item in resultado.data:
            pregunta_cacheada = item["pregunta"].removeprefix(namespace)
            vector_cached = _generar_embedding(
                modelo,
                pregunta_cacheada,
            )
            score = similitud_coseno(vector_pregunta, vector_cached)
            if score > mejor_score:
                mejor_score = score
                mejor_respuesta = item["respuesta"]

        if mejor_score >= threshold:
            logger.info("Respuesta recuperada del cache semantico")
            return mejor_respuesta
        return None
    except Exception:
        logger.warning(
            "Error consultando cache semantico",
            exc_info=True,
        )
        return None


def guardar_cache_semantico(
    pregunta: str,
    respuesta: str,
    user_id: str,
) -> None:
    try:
        supabase.table("cache_semantico").insert(
            {
                "pregunta": (
                    f"{_namespace(user_id)}"
                    f"{pregunta.strip().lower()}"
                ),
                "respuesta": respuesta,
                "hits": 1,
            }
        ).execute()
    except Exception:
        logger.warning(
            "Error guardando cache semantico",
            exc_info=True,
        )
