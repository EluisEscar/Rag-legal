import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.validation import clean_optional_uuid, clean_text
from app.repositories.cache import (
    generar_clave_cache,
    guardar_cache,
    obtener_cache,
)
from app.repositories.historial import (
    actualizar_timestamp,
    conversacion_pertenece_a_usuario,
    guardar_mensaje,
    guardar_resumen,
    obtener_historial,
)
from app.services.cache_semantico import (
    buscar_cache_semantico,
    guardar_cache_semantico,
)
from app.services.agente import RESPUESTA_NO_LEGAL, agente_legal
from app.services.resumidor import resumir_historial

router = APIRouter(tags=["preguntas"])


@router.post("/preguntar-agente")
async def preguntar_agente(
    request: Request,
    pregunta: str = Form(..., min_length=1, max_length=4000),
    conversacion_id: str = Form(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    pregunta = clean_text(
        pregunta,
        field="pregunta",
        max_length=4000,
    )
    conversacion_id = clean_optional_uuid(
        conversacion_id,
        field="conversacion_id",
    )
    if conversacion_id and not conversacion_pertenece_a_usuario(
        conversacion_id,
        current_user.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada",
        )

    session_id = current_user.id
    sesion = request.app.state.sesiones.get(session_id)
    tiene_documento = sesion is not None

    historial_temp = []
    if conversacion_id:
        historial_temp = obtener_historial(conversacion_id, limite=4)
    elif sesion:
        historial_temp = sesion["historial"][-4:]

    clave_cache = generar_clave_cache(
        pregunta,
        current_user.id,
        historial_temp,
        modo="agente",
    )
    permite_cache_semantico = not historial_temp

    if not tiene_documento:
        respuesta_cacheada = obtener_cache(clave_cache)
        if respuesta_cacheada:
            if conversacion_id:
                _guardar_interaccion(
                    conversacion_id,
                    pregunta,
                    respuesta_cacheada,
                )
            return _stream_respuesta_agente(
                pregunta=pregunta,
                pregunta_mejorada=pregunta,
                respuesta=respuesta_cacheada,
                chunks=[],
                desde_cache=True,
                tipo_cache="exacto",
            )

        respuesta_semantica = (
            buscar_cache_semantico(
                pregunta,
                current_user.id,
                request.app.state.embedding_model,
                modo="agente",
            )
            if permite_cache_semantico
            else None
        )
        if respuesta_semantica:
            if conversacion_id:
                _guardar_interaccion(
                    conversacion_id,
                    pregunta,
                    respuesta_semantica,
                )
            return _stream_respuesta_agente(
                pregunta=pregunta,
                pregunta_mejorada=pregunta,
                respuesta=respuesta_semantica,
                chunks=[],
                desde_cache=True,
                tipo_cache="semantico",
            )

    historial = _preparar_historial(
        conversacion_id,
        sesion,
        request.app.state.groq,
    )
    estado_final = await run_in_threadpool(
        agente_legal.invoke,
        {
            "pregunta_original": pregunta,
            "pregunta_mejorada": "",
            "contexto": "",
            "chunks": [],
            "respuesta": "",
            "es_valida": False,
            "necesita_mas_info": False,
            "historial": historial,
            "tiene_documento": tiene_documento,
            "groq_client": request.app.state.groq,
            "sesion": sesion,
            "motor_legal": request.app.state.motor_legal,
        },
    )

    respuesta = estado_final.get("respuesta", "")
    pregunta_mejorada = estado_final.get("pregunta_mejorada") or pregunta
    es_no_legal = respuesta == RESPUESTA_NO_LEGAL

    if conversacion_id and respuesta:
        _guardar_interaccion(conversacion_id, pregunta, respuesta)
    elif sesion and respuesta:
        sesion["historial"].extend([
            {"role": "user", "content": pregunta},
            {"role": "assistant", "content": respuesta},
        ])

    debe_cachear = (
        bool(respuesta)
        and not tiene_documento
        and not es_no_legal
    )
    if debe_cachear:
        guardar_cache(clave_cache, respuesta)
        if permite_cache_semantico:
            guardar_cache_semantico(
                pregunta,
                respuesta,
                current_user.id,
                modo="agente",
            )

    return _stream_respuesta_agente(
        pregunta=pregunta,
        pregunta_mejorada=pregunta_mejorada,
        respuesta=respuesta,
        chunks=estado_final.get("chunks", []),
        desde_cache=False,
        tipo_cache="ninguno",
        tipo_pregunta=estado_final.get("tipo_pregunta"),
        modelo_usado=estado_final.get("modelo_usado"),
    )

def _stream_respuesta_agente(
    *,
    pregunta: str,
    pregunta_mejorada: str,
    respuesta: str,
    chunks: list,
    desde_cache: bool,
    tipo_cache: str,
    tipo_pregunta: str | None = None,
    modelo_usado: str | None = None,
) -> StreamingResponse:
    def generar_stream():
        if respuesta:
            yield json.dumps({
                "tipo": "chunk",
                "texto": respuesta,
            }) + "\n"

        yield json.dumps({
            "tipo": "fin",
            "pregunta": pregunta,
            "pregunta_mejorada": pregunta_mejorada,
            "chunks": chunks,
            "desde_cache": desde_cache,
            "tipo_cache": tipo_cache,
            "respuesta": respuesta,
            "tipo_pregunta": tipo_pregunta,
            "modelo_usado": modelo_usado,
        }) + "\n"

    return StreamingResponse(
        generar_stream(),
        media_type="application/x-ndjson",
    )


def _guardar_interaccion(
    conversacion_id: str | None,
    pregunta: str,
    respuesta: str,
) -> None:
    if not conversacion_id:
        return

    guardar_mensaje(conversacion_id, "user", pregunta)
    guardar_mensaje(conversacion_id, "bot", respuesta)
    actualizar_timestamp(conversacion_id)


def _preparar_historial(
    conversacion_id: str | None,
    sesion,
    groq_client,
) -> list:
    if not conversacion_id:
        return sesion["historial"][-4:] if sesion else []

    historial_raw = obtener_historial(conversacion_id, limite=100)
    if len(historial_raw) <= 10:
        return historial_raw

    mensajes_antiguos = historial_raw[:-4]
    ultimos_cuatro = historial_raw[-4:]
    resumen = resumir_historial(mensajes_antiguos, groq_client)
    guardar_resumen(conversacion_id, resumen)

    historial = []
    if resumen:
        historial.append(
            {
                "role": "system",
                "content": (
                    "Resumen de la conversacion anterior: "
                    f"{resumen}"
                ),
            }
        )
    historial.extend(ultimos_cuatro)
    return historial
