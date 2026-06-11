from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import CurrentUser, get_current_user


router = APIRouter(prefix="/sesiones", tags=["sesiones"])


@router.get("")
def listar_sesiones(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    sesion = request.app.state.sesiones.get(current_user.id)
    if not sesion:
        return {}
    return {
        current_user.id: {
            "filename": sesion["filename"],
            "mensajes_historial": len(sesion["historial"]),
        }
    }


@router.delete("/{session_id}")
def eliminar_sesion(
    session_id: str,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    if session_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesion no encontrada",
        )
    if request.app.state.sesiones.delete(session_id):
        return {"ok": True, "mensaje": f"Sesion {session_id} eliminada"}
    return {"error": "Sesion no encontrada"}
