from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.repositories import MessageRepository
from app.schemas import ChartDataResponse


class FrequencyAnalytics:
    @staticmethod
    def daily_from_messages(messages: list[ChatMessage]) -> dict:
        counts: Counter = Counter()
        for msg in messages:
            key = msg.timestamp.strftime("%Y-%m-%d")
            counts[key] += 1
        labels = sorted(counts.keys())
        return {"labels": labels, "values": [counts[label] for label in labels]}

    @staticmethod
    def weekly_from_messages(messages: list[ChatMessage]) -> dict:
        counts: Counter = Counter()
        for msg in messages:
            year, week, _ = msg.timestamp.isocalendar()
            key = f"{year}-W{week:02d}"
            counts[key] += 1
        labels = sorted(counts.keys())
        return {"labels": labels, "values": [counts[label] for label in labels]}

    @staticmethod
    def monthly_from_messages(messages: list[ChatMessage]) -> dict:
        counts: Counter = Counter()
        for msg in messages:
            key = msg.timestamp.strftime("%Y-%m")
            counts[key] += 1
        labels = sorted(counts.keys())
        return {"labels": labels, "values": [counts[label] for label in labels]}

    @staticmethod
    async def daily(db: AsyncSession, group_id: int) -> ChartDataResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        data = FrequencyAnalytics.daily_from_messages(messages)
        return ChartDataResponse(**data)

    @staticmethod
    async def weekly(db: AsyncSession, group_id: int) -> ChartDataResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        data = FrequencyAnalytics.weekly_from_messages(messages)
        return ChartDataResponse(**data)

    @staticmethod
    async def monthly(db: AsyncSession, group_id: int) -> ChartDataResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        data = FrequencyAnalytics.monthly_from_messages(messages)
        return ChartDataResponse(**data)
