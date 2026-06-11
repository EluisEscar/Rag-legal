from fastapi import APIRouter, Depends, Form, HTTPException, status

from app.core.auth import CurrentUser, get_current_user
from app.repositories.historial import (
    conversacion_pertenece_a_usuario,
    crear_conversacion,
    eliminar_conversacion,
    obtener_conversaciones,
    obtener_historial,
    renombrar_conversacion,
)


router = APIRouter(prefix="/conversaciones", tags=["conversaciones"])


@router.get("")
def listar_conversaciones(
    current_user: CurrentUser = Depends(get_current_user),
):
    return obtener_conversaciones(current_user.id)


@router.post("")
def nueva_conversacion(
    titulo: str = Form(default="Nueva consulta"),
    current_user: CurrentUser = Depends(get_current_user),
):
    conversacion_id = crear_conversacion(current_user.id, titulo)
    return {"id": conversacion_id, "titulo": titulo}


@router.get("/{conversacion_id}/mensajes")
def listar_mensajes(
    conversacion_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _validar_propietario(conversacion_id, current_user.id)
    return obtener_historial(conversacion_id, limite=500)


@router.put("/{conversacion_id}")
def renombrar(
    conversacion_id: str,
    titulo: str = Form(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    _validar_propietario(conversacion_id, current_user.id)
    renombrar_conversacion(conversacion_id, current_user.id, titulo)
    return {"ok": True}


@router.delete("/{conversacion_id}")
def eliminar(
    conversacion_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _validar_propietario(conversacion_id, current_user.id)
    eliminar_conversacion(conversacion_id, current_user.id)
    return {"ok": True}


def _validar_propietario(conversacion_id: str, user_id: str) -> None:
    if not conversacion_pertenece_a_usuario(conversacion_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )
