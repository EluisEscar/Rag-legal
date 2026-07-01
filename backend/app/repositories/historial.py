import logging
from datetime import datetime, timezone

from app.core.errors import RepositoryError
from app.repositories.client import supabase


logger = logging.getLogger(__name__)


def crear_conversacion(
    user_id: str,
    titulo: str = "Nueva consulta",
) -> str:
    try:
        resultado = supabase.table("conversaciones").insert(
            {
                "user_id": user_id,
                "titulo": titulo,
            }
        ).execute()
        return resultado.data[0]["id"]
    except Exception as error:
        _raise_repository_error("crear la conversacion", error)


def guardar_mensaje(
    conversacion_id: str,
    rol: str,
    texto: str,
) -> None:
    try:
        supabase.table("mensajes").insert(
            {
                "conversacion_id": conversacion_id,
                "rol": rol,
                "texto": texto,
            }
        ).execute()
    except Exception as error:
        _raise_repository_error("guardar el mensaje", error)


def obtener_historial(
    conversacion_id: str,
    limite: int = 4,
) -> list:
    try:
        resultado = (
            supabase.table("mensajes")
            .select("rol, texto")
            .eq("conversacion_id", conversacion_id)
            .order("created_at", desc=True)
            .limit(limite)
            .execute()
        )
    except Exception as error:
        _raise_repository_error("obtener el historial", error)

    return [
        {
            "role": "user" if mensaje["rol"] == "user" else "assistant",
            "content": mensaje["texto"],
        }
        for mensaje in resultado.data[::-1]
        if mensaje["rol"] in ("user", "bot")
    ]


def obtener_conversaciones(user_id: str) -> list:
    try:
        resultado = (
            supabase.table("conversaciones")
            .select("id, titulo, created_at, updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return resultado.data
    except Exception as error:
        _raise_repository_error("obtener las conversaciones", error)


def conversacion_pertenece_a_usuario(
    conversacion_id: str,
    user_id: str,
) -> bool:
    try:
        resultado = (
            supabase.table("conversaciones")
            .select("id")
            .eq("id", conversacion_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return bool(resultado.data)
    except Exception as error:
        _raise_repository_error("validar la conversacion", error)


def renombrar_conversacion(
    conversacion_id: str,
    user_id: str,
    nuevo_titulo: str,
) -> None:
    try:
        (
            supabase.table("conversaciones")
            .update({"titulo": nuevo_titulo})
            .eq("id", conversacion_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as error:
        _raise_repository_error("renombrar la conversacion", error)


def eliminar_conversacion(
    conversacion_id: str,
    user_id: str,
) -> None:
    try:
        (
            supabase.table("conversaciones")
            .delete()
            .eq("id", conversacion_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as error:
        _raise_repository_error("eliminar la conversacion", error)


def actualizar_timestamp(conversacion_id: str) -> None:
    try:
        (
            supabase.table("conversaciones")
            .update(
                {
                    "updated_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                }
            )
            .eq("id", conversacion_id)
            .execute()
        )
    except Exception as error:
        _raise_repository_error(
            "actualizar la conversacion",
            error,
        )


def guardar_resumen(
    conversacion_id: str,
    resumen: str,
) -> None:
    try:
        (
            supabase.table("conversaciones")
            .update({"resumen": resumen})
            .eq("id", conversacion_id)
            .execute()
        )
    except Exception as error:
        _raise_repository_error("guardar el resumen", error)


def _raise_repository_error(action: str, error: Exception):
    logger.exception("No se pudo %s", action)
    raise RepositoryError(f"No se pudo {action}") from error
