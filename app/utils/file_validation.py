import re
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

ALLOWED_EXTENSIONS = {".txt"}
TEXT_CONTENT_TYPES = {"text/plain", "application/octet-stream", "text/csv"}


async def validate_upload_file(file: UploadFile) -> bytes:
    settings = get_settings()

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Filename is required")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .txt WhatsApp export files are allowed",
        )

    if file.content_type and file.content_type not in TEXT_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid content type: {file.content_type}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File is empty")

    if len(content) > settings.upload_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File exceeds maximum size of {settings.UPLOAD_MAX_SIZE_MB}MB",
        )

    return content


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text, flags=re.IGNORECASE)
