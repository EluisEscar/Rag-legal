import json
import re
import asyncio
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.services.clasificador import elegir_modelo
from app.services.prompts import construir_contexto, construir_prompt

from app.services.scraper_peruano import buscar_normas_peruano, formatear_contexto_normas

MODELO_CONTROL = "llama-3.1-8b-instant"
RESPUESTA_NO_LEGAL = "Solo puedo responder consultas sobre derecho peruano."


class EstadoLegal(TypedDict, total=False):
    pregunta_original:    str
    pregunta_mejorada:    str
    contexto:             str
    chunks:               list
    respuesta:            str
    es_valida:            bool
    necesita_mas_info:    bool
    historial:            list
    tiene_documento:      bool
    tipo_pregunta:        str
    modelo_usado:         str
    groq_client:          Any
    sesion:               Any
    motor_legal:          Any


# ── Nodo 1: Validar si es consulta legal ──
def validar(state: EstadoLegal) -> EstadoLegal:
    pregunta = state["pregunta_original"]
    prompt = f"""
Responde solo JSON valido.
Determina si la pregunta tiene relacion con temas legales peruanos.
Acepta lenguaje coloquial. Ejemplos que SI son legales:
- "me echaron del trabajo sin razon" = despido laboral = true
- "me robaron el celular" = denuncia penal = true
- "no me pagan el sueldo" = reclamo laboral = true
- "quiero divorciarme" = derecho de familia = true
- "me estafaron en una compra" = derecho civil = true
- "me botaron de mi casa" = desalojo = true
- "firmé un contrato y no lo cumplen" = incumplimiento contractual = true
Solo es false si es completamente ajeno al derecho (recetas, deportes, etc).

Pregunta: {pregunta}

Formato:
{{"es_valida": true}}
"""
    respuesta = _llm_text(state["groq_client"], prompt, max_tokens=40)
    es_valida = _json_bool(respuesta, "es_valida")
    if es_valida is None:
        es_valida = _parece_consulta_legal(pregunta)
    return {"es_valida": es_valida}


# ── Nodo 2: Reescribir query con terminología jurídica ──
def reescribir(state: EstadoLegal) -> EstadoLegal:
    pregunta = state["pregunta_original"]
    prompt = f"""
Reescribe la consulta usando terminologia juridica peruana precisa para
mejorar una busqueda vectorial. Mantente fiel a los hechos del usuario.
No respondas la consulta. Devuelve solo la pregunta reescrita.

Ejemplos:
- "me echaron del trabajo" → "despido arbitrario sin causa justificada Peru Codigo Laboral"
- "me robaron" → "denuncia penal por robo hurto Peru Codigo Penal"
- "no me pagan" → "incumplimiento pago remuneraciones trabajador Peru"
- "quiero divorciarme" → "proceso divorcio causales Codigo Civil Peru"

Consulta: {pregunta}
"""
    respuesta = _llm_text(state["groq_client"], prompt, max_tokens=120)
    pregunta_mejorada = _limpiar_linea(respuesta) or pregunta
    return {"pregunta_mejorada": pregunta_mejorada}


# ── Nodo 3: Recuperar contexto con pregunta mejorada ──
def recuperar_contexto(state: EstadoLegal) -> EstadoLegal:
    pregunta = state.get("pregunta_mejorada") or state["pregunta_original"]
    chunks = []
    sesion     = state.get("sesion")
    motor_legal = state.get("motor_legal")

    if sesion:
        resultado_documento = sesion["motor"].query(pregunta)
        chunks.extend(_extraer_chunks(resultado_documento, "documento_abogado"))

    if motor_legal:
        resultado_legal = motor_legal.query(pregunta)
        chunks.extend(_extraer_chunks(resultado_legal, "base_legal"))

    return {
        "chunks":   chunks,
        "contexto": construir_contexto(chunks) if chunks else "",
    }


# ── Nodo 4: Evaluar si el contexto es suficiente ──
def evaluar_contexto(state: EstadoLegal) -> EstadoLegal:
    chunks          = state.get("chunks", [])
    contexto        = state.get("contexto", "")
    tiene_documento = state.get("tiene_documento", False)

    # Si hay documento subido siempre es suficiente
    if tiene_documento:
        return {"necesita_mas_info": False}

    # Si no hay chunks o el contexto es muy corto
    if not chunks or len(contexto.strip()) < 300:
        return {"necesita_mas_info": True}

    prompt = f"""
Responde solo JSON valido.
Evalua si el contexto recuperado es suficiente para responder la consulta
legal peruana sin inventar informacion.

Consulta original: {state["pregunta_original"]}
Consulta mejorada: {state.get("pregunta_mejorada", "")}

Contexto (primeros 2000 chars):
{contexto[:2000]}

Formato:
{{"necesita_mas_info": false}}
"""
    respuesta       = _llm_text(state["groq_client"], prompt, max_tokens=40)
    necesita_mas_info = _json_bool(respuesta, "necesita_mas_info")
    if necesita_mas_info is None:
        necesita_mas_info = False
    return {"necesita_mas_info": necesita_mas_info}


# ── Nodo 5: Generar respuesta final ──
def responder(state: EstadoLegal) -> EstadoLegal:
    chunks = state.get("chunks", [])
    contexto = state.get("contexto") or construir_contexto(chunks)
    if not chunks and not contexto:
        return {"respuesta": "No encontre informacion relevante."}

    pregunta = state.get("pregunta_mejorada") or state["pregunta_original"]

    mensajes = [
        {
            "role":    "system",
            "content": construir_prompt(pregunta, contexto),
        },
        *state.get("historial", []),
        {
            "role":    "user",
            "content": state["pregunta_original"],
        },
    ]

    modelo, tipo_pregunta = elegir_modelo(state["pregunta_original"])

    respuesta_groq = state["groq_client"].chat.completions.create(
        model=modelo,
        messages=mensajes,
        max_tokens=1000,
        temperature=0.1,
    )

    return {
        "respuesta":     respuesta_groq.choices[0].message.content,
        "modelo_usado":  modelo,
        "tipo_pregunta": tipo_pregunta,
    }


# ── Nodo 6: Respuesta para consultas no legales ──
def no_legal(state: EstadoLegal) -> EstadoLegal:
    return {"respuesta": RESPUESTA_NO_LEGAL}

def buscar_peruano(state: EstadoLegal) -> EstadoLegal:
    """
    Busca normas recientes en El Peruano cuando el contexto
    de Qdrant es insuficiente.
    Solo se activa si necesita_mas_info = True.
    """
    print("📰 Buscando en El Peruano...")

    pregunta = state.get("pregunta_mejorada") or state["pregunta_original"]

    try:
        # Ejecutar scraping asíncrono desde contexto síncrono
        normas = asyncio.run(
            buscar_normas_peruano(pregunta, max_resultados=3)
        )

        if normas:
            contexto_peruano = formatear_contexto_normas(normas)
            contexto_actual  = state.get("contexto", "")
            chunks_actuales = state.get("chunks", [])

            print(f"   ✅ {len(normas)} normas encontradas en El Peruano")

            return {
                "contexto":          contexto_actual + "\n\n" + contexto_peruano,
                "chunks": chunks_actuales + [
                    {
                        "texto": contexto_peruano,
                        "score": None,
                        "filename": "El Peruano",
                        "fuente": "El Peruano",
                    },
                ],
                "necesita_mas_info": False,
            }
        else:
            print("   ⚠ Sin resultados en El Peruano")

    except Exception as e:
        print(f"   ⚠ Error en scraper: {e}")

    return {}

# ── Decisiones del grafo ──
def ruta_validacion(state: EstadoLegal) -> str:
    return "es_legal" if state.get("es_valida") else "no_es_legal"

def ruta_contexto(state: EstadoLegal) -> str:
    if state.get("necesita_mas_info"):
        return "buscar_peruano"
    return "responder"

# ── Construir el grafo ──
def construir_agente():
    graph = StateGraph(EstadoLegal)

    graph.add_node("validar",            validar)
    graph.add_node("reescribir",         reescribir)
    graph.add_node("recuperar_contexto", recuperar_contexto)
    graph.add_node("evaluar_contexto",   evaluar_contexto)
    graph.add_node("buscar_peruano",     buscar_peruano)  # ← nuevo
    graph.add_node("responder",          responder)
    graph.add_node("no_legal",           no_legal)

    graph.set_entry_point("validar")

    graph.add_conditional_edges(
        "validar",
        ruta_validacion,
        {
            "es_legal":    "reescribir",
            "no_es_legal": "no_legal",
        },
    )

    graph.add_edge("reescribir",         "recuperar_contexto")
    graph.add_edge("recuperar_contexto", "evaluar_contexto")

    # Nueva ruta: si necesita más info → buscar en El Peruano primero
    graph.add_conditional_edges(
        "evaluar_contexto",
        ruta_contexto,
        {
            "buscar_peruano": "buscar_peruano",  # ← nuevo
            "responder":      "responder",
        },
    )

    # Después de buscar en El Peruano → responder directamente
    graph.add_edge("buscar_peruano", "responder")

    graph.add_edge("responder",  END)
    graph.add_edge("no_legal",   END)

    return graph.compile()

# Instancia global del agente
agente_legal = construir_agente()

# ── Helpers privados ──
def _llm_text(groq_client, prompt: str, max_tokens: int = 120) -> str:
    respuesta = groq_client.chat.completions.create(
        model=MODELO_CONTROL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0,
    )
    return (respuesta.choices[0].message.content or "").strip()


def _json_bool(texto: str, key: str) -> bool | None:
    try:
        data = json.loads(_extraer_json(texto))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    value = data.get(key)
    return value if isinstance(value, bool) else None


def _extraer_json(texto: str) -> str:
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    return match.group(0) if match else texto


def _limpiar_linea(texto: str) -> str:
    return texto.strip().strip('"').strip("'").splitlines()[0].strip()


def _parece_consulta_legal(pregunta: str) -> bool:
    """Fallback cuando el LLM no devuelve JSON válido"""
    texto = pregunta.lower()
    claves = (
        # Términos jurídicos formales
        "derecho", "legal", "ley", "codigo", "articulo",
        "contrato", "demanda", "despido", "laboral", "civil",
        "penal", "peru", "peruano", "juez", "proceso",
        "sentencia", "indemnizacion", "tribunal", "juzgado",
        "abogado", "fiscal", "notario", "herencia", "testamento",
        "divorcio", "pension", "alimentos", "custodia",
        "arrendamiento", "inquilino", "propietario", "hipoteca",
        "deuda", "cobro", "embargo", "multa", "infraccion",
        "denuncia", "querella", "amparo", "habeas",
        # Lenguaje coloquial laboral
        "echaron", "botaron", "despidieron", "renuncie", "renuncia",
        "trabajo", "trabajar", "empleado", "empleador", "jefe",
        "sueldo", "salario", "pago", "liquidacion", "cts",
        "vacaciones", "gratificacion", "essalud", "afp",
        # Lenguaje coloquial general
        "robaron", "estafaron", "estafa", "engañaron", "accidente",
        "golpearon", "amenazaron", "acosaron", "discriminaron",
        "me deben", "no me pagan", "me quitaron", "me cobraron",
        "firme", "firme un", "debo", "prestamo", "prestaron",
        "alquiler", "cuotas", "interes", "sin razon", "sin causa",
        "me echaron", "me botaron", "me despidieron",
    )
    return any(clave in texto for clave in claves)


def _extraer_chunks(resultado, fuente_predeterminada: str) -> list:
    if not hasattr(resultado, "source_nodes"):
        return []
    return [
        {
            "texto":    nodo.text,
            "score":    round(nodo.score, 4) if nodo.score else None,
            "filename": nodo.metadata.get("filename", ""),
            "fuente":   nodo.metadata.get("fuente", fuente_predeterminada),
        }
        for nodo in resultado.source_nodes
    ]
