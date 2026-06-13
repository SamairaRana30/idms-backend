import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["ADMIN_EMAIL"] = "admin@test.com"

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.database.session import Base, get_db
from app.main import app
from app.models import User, UserRole

get_settings.cache_clear()

TEST_ENGINE = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(TEST_ENGINE, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    from app.repositories import UserRepository

    repo = UserRepository(db_session)
    existing = await repo.get_by_username("admin")
    if existing:
        return existing

    user = User(
        username="admin",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def analyst_user(db_session: AsyncSession) -> User:
    user = User(
        username="analyst",
        email="analyst@test.com",
        password_hash=get_password_hash("analyst123"),
        role=UserRole.ANALYST,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def analyst_token(client: AsyncClient, analyst_user: User) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "analyst", "password": "analyst123"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def imported_group(client: AsyncClient, admin_token: str):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_android_chat.txt")
    with open(sample_path, "rb") as f:
        response = await client.post(
            "/api/v1/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"group_name": "Test Group"},
            files={"file": ("chat.txt", f, "text/plain")},
        )
    assert response.status_code == 200
    return response.json()
