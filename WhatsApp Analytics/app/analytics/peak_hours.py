from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.repositories import MessageRepository
from app.schemas import PeakHourItem, PeakHoursResponse


class PeakHoursAnalytics:
    @staticmethod
    def from_messages(messages: list[ChatMessage]) -> PeakHoursResponse:
        counts: Counter = Counter(msg.timestamp.hour for msg in messages)
        peak_hours = [PeakHourItem(hour=h, message_count=counts.get(h, 0)) for h in range(24)]
        busiest = max(peak_hours, key=lambda x: x.message_count).hour if messages else 0
        return PeakHoursResponse(peak_hours=peak_hours, busiest_hour=busiest)

    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> PeakHoursResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        return PeakHoursAnalytics.from_messages(messages)
