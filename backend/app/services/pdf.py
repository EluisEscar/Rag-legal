import fitz


def extraer_texto_pdf(archivo_bytes: bytes) -> str:
    documento = fitz.open(stream=archivo_bytes, filetype="pdf")
    try:
        return "".join(pagina.get_text() for pagina in documento)
    finally:
        documento.close()
