from groq import Groq
import os

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def resumir_historial(historial: list) -> str:
    """
    Resume una lista de mensajes en un párrafo corto.
    Usa el modelo pequeño para ahorrar tokens.
    """
    if not historial:
        return ""

    texto = ""
    for msg in historial:
        rol    = "Abogado" if msg["role"] == "user" else "LexPerú"
        texto += f"{rol}: {msg['content']}\n"

    try:
        respuesta = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role":    "system",
                    "content": (
                        "Resume la siguiente conversación legal en máximo 3 oraciones. "
                        "Ve directo al punto, sin introducción ni frases como 'aquí te presento'. "
                        "Solo el resumen de los temas legales tratados."
                    )
                },
                {
                    "role":    "user",
                    "content": texto
                }
            ],
            max_tokens=150,
            temperature=0.1
        )
        return respuesta.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠ Error resumiendo historial: {e}")
        return ""