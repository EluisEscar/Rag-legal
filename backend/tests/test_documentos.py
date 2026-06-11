import asyncio
import unittest
from io import BytesIO

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.api.documentos import (
    _leer_archivo_limitado,
    _validar_metadatos_pdf,
)
from app.core.config import get_settings


def upload_file(
    content: bytes,
    filename: str,
    content_type: str,
) -> UploadFile:
    return UploadFile(
        BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


class DocumentValidationTests(unittest.TestCase):
    def test_rejects_non_pdf_extension(self):
        archivo = upload_file(b"texto", "archivo.txt", "text/plain")

        with self.assertRaises(HTTPException) as context:
            _validar_metadatos_pdf(archivo)

        self.assertEqual(context.exception.status_code, 400)

    def test_rejects_file_over_size_limit(self):
        max_bytes = get_settings().max_pdf_bytes
        archivo = upload_file(
            b"x" * (max_bytes + 1),
            "archivo.pdf",
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            asyncio.run(_leer_archivo_limitado(archivo))

        self.assertEqual(context.exception.status_code, 413)
