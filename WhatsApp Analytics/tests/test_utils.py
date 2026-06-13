import pytest
from httpx import AsyncClient

from app.utils.file_validation import extract_urls, validate_upload_file
from fastapi import UploadFile
from io import BytesIO


def test_extract_urls():
    urls = extract_urls("Check https://example.com and http://test.org")
    assert len(urls) == 2


@pytest.mark.asyncio
async def test_validate_upload_file_success():
    file = UploadFile(filename="chat.txt", file=BytesIO(b"test content"))
    content = await validate_upload_file(file)
    assert content == b"test content"


@pytest.mark.asyncio
async def test_validate_upload_invalid_extension():
    from fastapi import HTTPException

    file = UploadFile(filename="chat.pdf", file=BytesIO(b"data"))
    with pytest.raises(HTTPException) as exc:
        await validate_upload_file(file)
    assert exc.value.status_code == 422
