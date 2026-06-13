from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessageType
from app.repositories import MessageRepository
from app.schemas import MediaComparisonResponse, MediaTypeCount


class MediaAnalytics:
    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> MediaComparisonResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        total = len(messages)
        counts = Counter(msg.message_type.value for msg in messages)

        all_types = [t.value for t in MessageType]
        breakdown = []
        for msg_type in all_types:
            count = counts.get(msg_type, 0)
            percentage = round((count / total * 100) if total else 0, 2)
            breakdown.append(MediaTypeCount(type=msg_type, count=count, percentage=percentage))

        return MediaComparisonResponse(total_messages=total, breakdown=breakdown)
