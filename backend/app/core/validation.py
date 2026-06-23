import re
from pathlib import PurePath

from fastapi import HTTPException, status


CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


def clean_text(
    value: str | None,
    *,
    field: str,
    max_length: int,
    allow_empty: bool = False,
) -> str:
    text = (value or "").strip()
    if CONTROL_CHARS.search(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} contiene caracteres no permitidos",
        )
    if not allow_empty and not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} es requerido",
        )
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"{field} supera el limite permitido",
        )
    return text


def clean_optional_uuid(value: str | None, *, field: str) -> str | None:
    if value in (None, ""):
        return None
    text = clean_text(value, field=field, max_length=64)
    if not UUID_RE.fullmatch(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} tiene un formato invalido",
        )
    return text


def clean_required_uuid(value: str, *, field: str) -> str:
    text = clean_text(value, field=field, max_length=64)
    if not UUID_RE.fullmatch(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} tiene un formato invalido",
        )
    return text


def clean_filename(value: str | None, *, max_length: int = 180) -> str:
    filename = PurePath((value or "").replace("\\", "/")).name.strip()
    filename = clean_text(
        filename,
        field="filename",
        max_length=max_length,
    )
    if filename in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo invalido",
        )
    return filename
