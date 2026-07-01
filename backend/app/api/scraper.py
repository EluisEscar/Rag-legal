import logging
from fastapi import APIRouter, Depends, Query

from app.core.auth import CurrentUser, get_current_user
from app.services.scraper_peruano import buscar_normas_peruano, formatear_contexto_normas

logger = logging.getLogger(__name__)
router = APIRouter(tags=["scraper"])

@router.get("/buscar-peruano")
async def buscar_en_peruano(
    query: str = Query(..., min_length=3, max_length=200),
    max_resultados: int = Query(default=3, ge=1, le=5),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Busca normas legales en El Peruano relacionadas con el query.
    Útil para obtener normas recientes no indexadas en Qdrant.
    """
    normas = await buscar_normas_peruano(query, max_resultados)

    return {
        "query":    query,
        "total":    len(normas),
        "normas":   normas,
        "contexto": formatear_contexto_normas(normas),
    }
