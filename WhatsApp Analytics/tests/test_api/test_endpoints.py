import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_activity_analytics(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/activity?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] > 0
    assert len(data["top_10_active_users"]) > 0


@pytest.mark.asyncio
async def test_frequency_endpoints(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    for path in ["daily", "weekly", "monthly"]:
        response = await client.get(
            f"/api/v1/analytics/frequency/{path}?group_id={group_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert "labels" in response.json()
        assert "values" in response.json()


@pytest.mark.asyncio
async def test_peak_hours(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/peak-hours?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["peak_hours"]) == 24


@pytest.mark.asyncio
async def test_media_comparison(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/media-comparison?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["total_messages"] > 0


@pytest.mark.asyncio
async def test_sentiment_endpoints(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/sentiment?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    response = await client.get(
        f"/api/v1/analytics/sentiment/users?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["users"]) > 0


@pytest.mark.asyncio
async def test_spam_analytics(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/spam?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_influential_users(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/influential-users?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["users"]) > 0


@pytest.mark.asyncio
async def test_network_analytics(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/network?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


@pytest.mark.asyncio
async def test_emotions_analytics(client: AsyncClient, admin_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/emotions?group_id={group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["topics"]) == 4


@pytest.mark.asyncio
async def test_analytics_group_not_found(client: AsyncClient, admin_token):
    response = await client.get(
        "/api/v1/analytics/activity?group_id=99999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analyst_can_read_analytics(client: AsyncClient, analyst_token, imported_group):
    group_id = imported_group["group_id"]
    response = await client.get(
        f"/api/v1/analytics/activity?group_id={group_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert response.status_code == 200
