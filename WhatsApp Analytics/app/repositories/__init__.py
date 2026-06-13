from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityReport,
    ChatMessage,
    SentimentReport,
    User,
    UserRole,
    UserStatistics,
    WhatsAppGroup,
)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def count_admins(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(User).where(User.role == UserRole.ADMIN))
        return result.scalar_one()


class GroupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, group_id: int) -> WhatsAppGroup | None:
        result = await self.db.execute(select(WhatsAppGroup).where(WhatsAppGroup.id == group_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[WhatsAppGroup]:
        result = await self.db.execute(select(WhatsAppGroup).order_by(WhatsAppGroup.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, group: WhatsAppGroup) -> WhatsAppGroup:
        self.db.add(group)
        await self.db.flush()
        await self.db.refresh(group)
        return group


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, messages: list[ChatMessage]) -> None:
        self.db.add_all(messages)
        await self.db.flush()

    async def get_by_group(self, group_id: int) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.group_id == group_id).order_by(ChatMessage.timestamp)
        )
        return list(result.scalars().all())

    async def count_by_group(self, group_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.group_id == group_id)
        )
        return result.scalar_one()


class StatisticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create_user_stats(self, stats: list[UserStatistics]) -> None:
        self.db.add_all(stats)
        await self.db.flush()

    async def get_by_group(self, group_id: int) -> list[UserStatistics]:
        result = await self.db.execute(
            select(UserStatistics)
            .where(UserStatistics.group_id == group_id)
            .order_by(UserStatistics.influence_score.desc())
        )
        return list(result.scalars().all())

    async def create_sentiment_report(self, report: SentimentReport) -> SentimentReport:
        self.db.add(report)
        await self.db.flush()
        return report

    async def create_activity_report(self, report: ActivityReport) -> ActivityReport:
        self.db.add(report)
        await self.db.flush()
        return report

    async def update_message_sentiment(self, message_id: int, sentiment, spam_score: float) -> None:
        result = await self.db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
        message = result.scalar_one_or_none()
        if message:
            message.sentiment = sentiment
            message.spam_score = spam_score
