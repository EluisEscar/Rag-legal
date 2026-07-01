import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from groq import Groq
from huggingface_hub import login
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.services.embeddings import EmbeddingPersonalizado
from app.services.session_store import SessionStore


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Iniciando backend")

    if settings.hf_token:
        login(token=settings.hf_token)
        logger.info("HuggingFace autenticado")

    logger.info("Cargando modelo de embeddings")
    embedding_model = EmbeddingPersonalizado(
        nombre_modelo=settings.embedding_model
    )
    Settings.embed_model = embedding_model
    Settings.llm = None
    Settings.node_parser = SentenceSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    logger.info("Conectando a base legal en Qdrant")
    qdrant_cliente = QdrantClient(url=settings.qdrant_url)
    vector_store = QdrantVectorStore(
        client=qdrant_cliente,
        collection_name=settings.qdrant_collection,
    )

    try:
        indice_legal = VectorStoreIndex.from_vector_store(
            vector_store=vector_store
        )
        app.state.motor_legal = indice_legal.as_query_engine(
            similarity_top_k=3,
            response_mode="no_text",
        )
        logger.info("Base legal cargada desde Qdrant")
    except Exception:
        logger.warning(
            "No se pudo cargar la base legal desde Qdrant",
            exc_info=True,
        )
        app.state.motor_legal = None

    app.state.groq = Groq(api_key=settings.groq_api_key)
    app.state.embedding_model = embedding_model
    app.state.sesiones = SessionStore(
        max_sessions=settings.max_sessions,
        ttl_seconds=settings.session_ttl_seconds,
    )

    logger.info("Backend listo")
    yield
