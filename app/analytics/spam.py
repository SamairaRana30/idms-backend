from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import MessageRepository
from app.schemas import SpamAnalyticsResponse, SpamMessageItem, SuspectedUserItem

SPAM_THRESHOLD = 50.0


class SpamAnalytics:
    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> SpamAnalyticsResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        spam_messages = [
            SpamMessageItem(
                id=msg.id,
                sender_name=msg.sender_name,
                message_text=msg.message_text[:500],
                spam_score=msg.spam_score,
                timestamp=msg.timestamp,
            )
            for msg in messages
            if msg.spam_score >= SPAM_THRESHOLD
        ]

        user_spam: dict[str, list[float]] = defaultdict(list)
        for item in spam_messages:
            user_spam[item.sender_name].append(item.spam_score)

        suspected = [
            SuspectedUserItem(
                sender_name=sender,
                spam_message_count=len(scores),
                average_spam_score=round(sum(scores) / len(scores), 2),
            )
            for sender, scores in user_spam.items()
        ]
        suspected.sort(key=lambda x: x.spam_message_count, reverse=True)

        return SpamAnalyticsResponse(spam_messages=spam_messages, suspected_users=suspected)
