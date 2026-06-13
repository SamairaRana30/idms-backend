from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.repositories import MessageRepository
from app.schemas import ActivityAnalyticsResponse, UserActivityItem


class ActivityAnalytics:
    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> ActivityAnalyticsResponse:
        repo = MessageRepository(db)
        messages = await repo.get_by_group(group_id)
        counts = Counter(msg.sender_name for msg in messages)
        ranked = counts.most_common()

        top_10 = [UserActivityItem(sender_name=name, message_count=count) for name, count in ranked[:10]]
        bottom_ranked = sorted(counts.items(), key=lambda x: x[1])[:10]
        bottom_10 = [UserActivityItem(sender_name=name, message_count=count) for name, count in bottom_ranked]

        return ActivityAnalyticsResponse(
            total_messages=len(messages),
            top_10_active_users=top_10,
            bottom_10_active_users=bottom_10,
        )
