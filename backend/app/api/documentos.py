from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.concurrency import run_in_threadpool
from llama_index.core import Document, VectorStoreIndex

from app.core.auth import CurrentUser, get_current_user
from app.core.config import get_settings
from app.services.pdf import extraer_texto_pdf


router = APIRouter(tags=["documentos"])

UPLOAD_CHUNK_BYTES = 1024 * 1024
PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/octet-stream",
}


@router.post("/subir-documento")
async def subir_documento(
    request: Request,
    archivo: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    session_id = current_user.id
    _validar_metadatos_pdf(archivo)
    contenido = await _leer_archivo_limitado(archivo)

    if not contenido.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no contiene un PDF valido",
        )

    sesion = await run_in_threadpool(
        _crear_sesion_documento,
        contenido,
        archivo.filename,
        session_id,
    )

    request.app.state.sesiones.set(session_id, sesion)

    return {
        "ok": True,
        "filename": archivo.filename,
        "session": session_id,
        "mensaje": "Documento listo para consultas",
    }


def _validar_metadatos_pdf(archivo: UploadFile) -> None:
    filename = archivo.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF",
        )

    if archivo.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido",
        )


async def _leer_archivo_limitado(archivo: UploadFile) -> bytes:
    partes = []
    total = 0

    while chunk := await archivo.read(UPLOAD_CHUNK_BYTES):
        total += len(chunk)
        if total > get_settings().max_pdf_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="El PDF supera el limite permitido",
            )
        partes.append(chunk)

    return b"".join(partes)


def _crear_sesion_documento(
    contenido: bytes,
    filename: str,
    session_id: str,
) -> dict:
    texto = extraer_texto_pdf(contenido)
    if not texto.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pudo extraer texto del PDF",
        )

    documento = Document(
        text=texto,
        metadata={
            "filename": filename,
            "session_id": session_id,
        },
    )
    indice = VectorStoreIndex.from_documents(
        [documento],
        show_progress=True,
    )
    motor = indice.as_query_engine(
        similarity_top_k=3,
        response_mode="no_text",
    )
    return {
        "motor": motor,
        "indice": indice,
        "filename": filename,
        "historial": [],
    }
