import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.conversaciones import router as conversaciones_router
from app.api.documentos import router as documentos_router
from app.api.preguntas import router as preguntas_router
from app.api.sesiones import router as sesiones_router
from app.core.lifespan import lifespan
from app.core.config import get_settings
from app.core.errors import RepositoryError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
settings = get_settings()


app = FastAPI(
    title="RAG Legal Peru",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documentos_router)
app.include_router(preguntas_router)
app.include_router(sesiones_router)
app.include_router(conversaciones_router)


@app.exception_handler(RepositoryError)
async def repository_error_handler(
    request: Request,
    error: RepositoryError,
):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "El servicio de datos no esta disponible",
        },
    )


@app.get("/")
def health():
    return {
        "status": "ok",
        "mensaje": "Backend RAG Legal Peru - LlamaIndex + GROQ",
    }
