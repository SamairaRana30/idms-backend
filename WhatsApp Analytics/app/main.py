from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import analytics, auth, upload
from app.api.web import dashboard
from app.core.config import get_settings
from app.database.session import AsyncSessionLocal
from app.schemas import ErrorResponse
from app.services.auth_service import AuthService

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = AuthService(session)
        await service.ensure_admin_exists(settings.ADMIN_PASSWORD, settings.ADMIN_EMAIL)
        await session.commit()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "WhatsApp Analytics Module for Organization X. "
            "Analyze exported WhatsApp group chats with advanced communication analytics. "
            "Sprint 4 - Developer: Yogesh"
        ),
        version="1.0.0",
        lifespan=lifespan,
        responses={
            401: {"model": ErrorResponse, "description": "Unauthorized"},
            403: {"model": ErrorResponse, "description": "Forbidden"},
            404: {"model": ErrorResponse, "description": "Not Found"},
            422: {"model": ErrorResponse, "description": "Validation Error"},
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.middleware.auth_middleware import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)

    static_dir = BASE_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(dashboard.router)

    return app


app = create_app()
