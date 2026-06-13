from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import User, UserRole
from app.repositories import UserRepository
from app.schemas import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self.user_repo.get_by_username(username)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.user_repo.get_by_username(user_data.username):
            raise ValueError("Username already registered")
        if await self.user_repo.get_by_email(user_data.email):
            raise ValueError("Email already registered")

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role,
        )
        return await self.user_repo.create(user)

    async def ensure_admin_exists(self, password: str, email: str) -> None:
        if await self.user_repo.count_admins() > 0:
            return

        admin = User(
            username="admin",
            email=email,
            password_hash=get_password_hash(password),
            role=UserRole.ADMIN,
        )
        await self.user_repo.create(admin)
