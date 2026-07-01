import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_BUSCADOR        = "https://busquedas.elperuano.pe"
TIMEOUT              = 10
DELAY_ENTRE_REQUESTS = 1.5

HEADERS = {
    "User-Agent": (
        "Intilex/1.0 (Asistente legal peruano; "
        "contacto: soporte@intilex.tech)"
    ),
    "Accept-Language": "es-PE,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}


async def buscar_normas_peruano(
    query: str,
    max_resultados: int = 3,
) -> list[dict]:
    """
    Busca normas en El Peruano relacionadas con el query.
    Retorna lista de dicts con titulo, fecha, url, resumen, fuente.
    """
    resultados = []

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:
            # Estrategia 1: buscar directamente en el buscador de El Peruano
            resultados = await _buscar_en_buscador_elperuano(
                client, query, max_resultados
            )

            # Estrategia 2: si no hay resultados, buscar normas por slug
            if not resultados:
                resultados = await _buscar_por_terminos(
                    client, query, max_resultados
                )

    except httpx.TimeoutException:
        logger.warning("Timeout al conectar con El Peruano")
    except Exception as e:
        logger.warning("Error scraping El Peruano: %s", e)

    return resultados


async def _buscar_en_buscador_elperuano(
    client: httpx.AsyncClient,
    query: str,
    max_resultados: int,
) -> list[dict]:
    """
    Busca en busquedas.elperuano.pe usando el endpoint de búsqueda.
    Las URLs de normas tienen el patrón:
    /normaslegales/{slug}-{tipo}-n-{numero}-{id}/
    """
    resultados = []

    try:
        # El buscador acepta búsqueda por texto en la URL
        resp = await client.get(
            f"{BASE_BUSCADOR}/busqueda/normaslegales",
            params={"q": query, "type": "NL"},
        )

        if resp.status_code != 200:
            # Intentar URL alternativa
            resp = await client.get(
                f"{BASE_BUSCADOR}/normaslegales",
                params={"q": query},
            )

        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Buscar links a normas
        links = soup.find_all(
            "a",
            href=re.compile(r"/normaslegales/|/dispositivo/NL/")
        )

        vistos = set()
        for link in links[:max_resultados * 2]:
            href  = link.get("href", "")
            titulo = link.get_text(strip=True)

            if not href or not titulo or href in vistos:
                continue
            if len(titulo) < 10:
                continue

            vistos.add(href)
            url = (
                href if href.startswith("http")
                else BASE_BUSCADOR + href
            )

            await asyncio.sleep(DELAY_ENTRE_REQUESTS)
            resumen = await _obtener_contenido_norma(client, url)

            resultados.append({
                "titulo":  titulo[:300],
                "fecha":   "",
                "url":     url,
                "resumen": resumen,
                "fuente":  "El Peruano",
            })

            if len(resultados) >= max_resultados:
                break

    except Exception as e:
        logger.debug("Error en buscador El Peruano: %s", e)

    return resultados


async def _buscar_por_terminos(
    client: httpx.AsyncClient,
    query: str,
    max_resultados: int,
) -> list[dict]:
    """
    Fallback: construye URLs directas de normas conocidas
    basadas en los términos del query.
    """
    resultados = []

    # Mapa de términos → normas conocidas importantes
    normas_conocidas = {
        "teletrabajo": [
            ("Ley del Teletrabajo N° 31572", "2104305-1"),
            ("Modificación Ley Teletrabajo N° 32102", "2309239-2"),
        ],
        "trabajo": [
            ("Ley de Productividad y Competitividad Laboral", "1307067-3"),
        ],
        "despido": [
            ("TUO Decreto Legislativo 728 - Ley de Trabajo", "1307067-3"),
        ],
        "arrendamiento": [
            ("Código Civil - Arrendamiento", "1984-codigo-civil"),
        ],
        "consumidor": [
            ("Código de Protección al Consumidor Ley 29571", "628647-1"),
        ],
        "contrato": [
            ("Código Civil Peruano - Contratos", "1984-codigo-civil"),
        ],
    }

    query_lower = query.lower()
    normas_a_buscar = []

    for termino, normas in normas_conocidas.items():
        if termino in query_lower:
            normas_a_buscar.extend(normas)

    for titulo, norma_id in normas_a_buscar[:max_resultados]:
        url = f"{BASE_BUSCADOR}/dispositivo/NL/{norma_id}"

        await asyncio.sleep(DELAY_ENTRE_REQUESTS)
        resumen = await _obtener_contenido_norma(client, url)

        if resumen:
            resultados.append({
                "titulo":  titulo,
                "fecha":   "",
                "url":     url,
                "resumen": resumen,
                "fuente":  "El Peruano",
            })

    return resultados


async def _obtener_contenido_norma(
    client: httpx.AsyncClient,
    url: str,
    max_chars: int = 1000,
) -> str:
    """
    Obtiene el contenido de una norma.
    Usa /api/visor_html/{id} si es una URL del buscador.
    """
    try:
        # Extraer ID de la norma desde la URL
        # Patrón 1: /dispositivo/NL/2104305-1
        match = re.search(r"/dispositivo/NL/(\d+-\d+)", url)

        # Patrón 2: /normaslegales/{slug}-{id}/
        if not match:
            match = re.search(r"-(\d+-\d+)/?$", url)

        if match:
            norma_id = match.group(1)
            api_url  = f"{BASE_BUSCADOR}/api/visor_html/{norma_id}"

            resp = await client.get(api_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.decompose()
                texto = soup.get_text(separator=" ", strip=True)
                return _limpiar_texto(texto)[:max_chars]

        # Fallback: scraping directo
        resp = await client.get(url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            contenido = (
                soup.select_one("article, main, .contenido")
                or soup.body
            )
            if contenido:
                texto = contenido.get_text(separator=" ", strip=True)
                return _limpiar_texto(texto)[:max_chars]

    except Exception as e:
        logger.debug("Error obteniendo norma %s: %s", url, e)

    return ""


def _limpiar_texto(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"[^\w\s\.,;:()°«»\"'\-\/]", " ", texto)
    return texto.strip()


def formatear_contexto_normas(normas: list[dict]) -> str:
    if not normas:
        return ""

    partes = ["NORMAS LEGALES RECIENTES (El Peruano):"]
    for i, norma in enumerate(normas, 1):
        partes.append(
            f"\n[Norma {i}] {norma['titulo']}"
            f"\nFuente: {norma.get('url', '')}"
        )
        if norma.get("resumen"):
            partes.append(f"Contenido: {norma['resumen']}")

    return "\n".join(partes)
