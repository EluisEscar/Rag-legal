import logging

from groq import Groq


logger = logging.getLogger(__name__)


def resumir_historial(
    historial: list,
    groq_client: Groq,
) -> str:
    if not historial:
        return ""

    lineas = []
    for mensaje in historial:
        rol = "Abogado" if mensaje["role"] == "user" else "Intilex"
        lineas.append(f"{rol}: {mensaje['content']}")

    try:
        respuesta = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Resume la siguiente conversacion legal en maximo "
                        "3 oraciones. Ve directo al punto y devuelve solo "
                        "el resumen de los temas legales tratados."
                    ),
                },
                {
                    "role": "user",
                    "content": "\n".join(lineas),
                },
            ],
            max_tokens=150,
            temperature=0.1,
        )
        return respuesta.choices[0].message.content.strip()
    except Exception:
        logger.warning(
            "No se pudo resumir el historial",
            exc_info=True,
        )
        return ""
