from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import User, UserRole
from app.repositories import UserRepository

security = HTTPBearer(auto_error=False)


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is not None:
        return credentials.credentials
    return request.cookies.get("access_token")


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await UserRepository(db).get_by_username(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    token = _extract_token(request, credentials)
    if not token:
        return None
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_analyst(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.ANALYST):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Analyst access required")
    return current_user


async def get_group_or_404(group_id: int, db: AsyncSession):
    from app.repositories import GroupRepository

    group = await GroupRepository(db).get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group
