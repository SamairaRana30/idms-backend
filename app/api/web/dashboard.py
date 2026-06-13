from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional, require_admin
from app.core.config import get_settings
from app.core.security import create_access_token
from app.database.session import get_db
from app.models import User, UserRole
from app.repositories import GroupRepository
from app.services.auth_service import AuthService

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["settings"] = get_settings()


def _get_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return request.cookies.get("access_token")


async def _get_user_from_request(request: Request, db: AsyncSession) -> User | None:
    token = _get_token(request)
    if not token:
        return None
    from app.core.security import decode_access_token
    from app.repositories import UserRepository

    payload = decode_access_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    return await UserRepository(db).get_by_username(username)


async def _require_page_user(request: Request, db: AsyncSession) -> User:
    user = await _get_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


async def _get_groups(db: AsyncSession) -> list:
    return await GroupRepository(db).list_all()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: str = Form(...),
    password: str = Form(...),
):
    service = AuthService(db)
    user = await service.authenticate(username, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_access_token({"sub": user.username, "role": user.role.value})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request, "user": user, "groups": groups, "settings": get_settings()},
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    if user.role != UserRole.ADMIN:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request, "upload.html", {"request": request, "user": user, "settings": get_settings()}
    )


@router.get("/analytics/activity", response_class=HTMLResponse)
async def activity_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "analytics_activity.html",
        {"request": request, "user": user, "groups": groups, "page": "activity", "settings": get_settings()},
    )


@router.get("/analytics/sentiment", response_class=HTMLResponse)
async def sentiment_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "analytics_sentiment.html",
        {"request": request, "user": user, "groups": groups, "page": "sentiment", "settings": get_settings()},
    )


@router.get("/analytics/spam", response_class=HTMLResponse)
async def spam_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "analytics_spam.html",
        {"request": request, "user": user, "groups": groups, "page": "spam", "settings": get_settings()},
    )


@router.get("/analytics/users", response_class=HTMLResponse)
async def users_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "analytics_users.html",
        {"request": request, "user": user, "groups": groups, "page": "users", "settings": get_settings()},
    )


@router.get("/analytics/network", response_class=HTMLResponse)
async def network_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "analytics_network.html",
        {"request": request, "user": user, "groups": groups, "page": "network", "settings": get_settings()},
    )


@router.get("/analytics/peak-hours", response_class=HTMLResponse)
async def peak_hours_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "analytics_peak_hours.html",
        {"request": request, "user": user, "groups": groups, "page": "peak-hours", "settings": get_settings()},
    )


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await _get_user_from_request(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    groups = await _get_groups(db)
    return templates.TemplateResponse(
        request,
        "reports.html",
        {"request": request, "user": user, "groups": groups, "page": "reports", "settings": get_settings()},
    )
