import re

# Palabras que indican preguntas simples
PALABRAS_SIMPLES = [
    "qué es", "que es",
    "qué significa", "que significa",
    "definición", "definicion",
    "significado",
    "cuándo", "cuando",
    "dónde", "donde",
    "quién", "quien",
    "cuál es", "cual es",
    "cómo se llama", "como se llama",
    "para qué sirve", "para que sirve",
]

# Palabras que indican preguntas complejas
PALABRAS_COMPLEJAS = [
    "analiza", "analizar",
    "compara", "comparar",
    "evalúa", "evalua",
    "determina", "determinar",
    "explica detalladamente",
    "cuáles son los requisitos",
    "es válido", "es valido",
    "procede", "corresponde",
    "qué consecuencias", "que consecuencias",
    "cómo puedo demandar", "como puedo demandar",
    "tengo derecho",
    "es posible",
    "interpreta",
    "cláusula", "clausula",
    "contrato",
    "indemnización", "indemnizacion",
    "nulidad",
    "prescripción", "prescripcion",
]

def clasificar_pregunta(pregunta: str) -> str:
    """
    Clasifica la pregunta como 'simple' o 'compleja'.
    Simple  → llama-3.1-8b-instant   (rápido, menos tokens)
    Compleja → qwen/qwen3.6-27b (mejor razonamiento)
    """
    pregunta_lower = pregunta.lower().strip()

    # Verificar si es compleja primero
    for palabra in PALABRAS_COMPLEJAS:
        if palabra in pregunta_lower:
            return "compleja"

    # Verificar si es simple
    for palabra in PALABRAS_SIMPLES:
        if palabra in pregunta_lower:
            return "simple"

    # Si la pregunta es corta → simple
    palabras = len(pregunta.split())
    if palabras <= 8:
        return "simple"

    # Por defecto → compleja (más seguro para temas legales)
    return "compleja"

def elegir_modelo(pregunta: str) -> tuple[str, str]:
    """
    Retorna (modelo, tipo) según la complejidad de la pregunta.
    """
    tipo = clasificar_pregunta(pregunta)

    if tipo == "simple":
        return "llama-3.1-8b-instant", "simple"
    else:
        return "qwen/qwen3.6-27b", "compleja"
