import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_success(client: AsyncClient, admin_token):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_android_chat.txt")
    with open(sample_path, "rb") as f:
        response = await client.post(
            "/api/v1/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"group_name": "Upload Test"},
            files={"file": ("chat.txt", f, "text/plain")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["message_count"] > 0
    assert data["group_name"] == "Upload Test"


@pytest.mark.asyncio
async def test_upload_analyst_forbidden(client: AsyncClient, analyst_token):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_android_chat.txt")
    with open(sample_path, "rb") as f:
        response = await client.post(
            "/api/v1/upload",
            headers={"Authorization": f"Bearer {analyst_token}"},
            data={"group_name": "Forbidden"},
            files={"file": ("chat.txt", f, "text/plain")},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_invalid_extension(client: AsyncClient, admin_token):
    response = await client.post(
        "/api/v1/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={"group_name": "Bad File"},
        files={"file": ("chat.pdf", b"fake pdf", "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient, admin_token, imported_group):
    response = await client.get(
        "/api/v1/upload/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1
