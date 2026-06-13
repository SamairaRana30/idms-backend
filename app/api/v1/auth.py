from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_admin
from app.core.security import create_access_token
from app.database.session import get_db
from app.models import User
from app.schemas import ErrorResponse, Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    responses={401: {"model": ErrorResponse}},
    summary="Authenticate user and receive JWT token",
)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(db)
    user = await service.authenticate(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username, "role": user.role.value})
    return Token(access_token=token)


@router.post(
    "/register",
    response_model=UserResponse,
    responses={403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Register a new user (Admin only)",
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
):
    service = AuthService(db)
    try:
        user = await service.create_user(user_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return user


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Get current authenticated user profile",
)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
