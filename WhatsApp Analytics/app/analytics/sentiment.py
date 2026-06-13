from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SentimentLabel
from app.repositories import MessageRepository
from app.schemas import ChartDataResponse, SentimentSummaryResponse, UserSentimentItem, UserSentimentResponse


class SentimentAnalytics:
    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> SentimentSummaryResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        counts = Counter(msg.sentiment for msg in messages if msg.sentiment)

        timeline_counts: dict[str, Counter] = defaultdict(Counter)
        for msg in messages:
            if msg.sentiment:
                day = msg.timestamp.strftime("%Y-%m-%d")
                timeline_counts[day][msg.sentiment.value] += 1

        labels = sorted(timeline_counts.keys())
        values = [sum(timeline_counts[day].values()) for day in labels]

        return SentimentSummaryResponse(
            positive_count=counts.get(SentimentLabel.POSITIVE, 0),
            negative_count=counts.get(SentimentLabel.NEGATIVE, 0),
            neutral_count=counts.get(SentimentLabel.NEUTRAL, 0),
            timeline=ChartDataResponse(labels=labels, values=values),
        )

    @staticmethod
    async def by_users(db: AsyncSession, group_id: int) -> UserSentimentResponse:
        messages = await MessageRepository(db).get_by_group(group_id)
        user_counts: dict[str, Counter] = defaultdict(Counter)

        for msg in messages:
            if msg.sentiment:
                user_counts[msg.sender_name][msg.sentiment.value] += 1

        users = [
            UserSentimentItem(
                sender_name=name,
                positive=counts.get("positive", 0),
                negative=counts.get("negative", 0),
                neutral=counts.get("neutral", 0),
            )
            for name, counts in sorted(user_counts.items(), key=lambda x: sum(x[1].values()), reverse=True)
        ]
        return UserSentimentResponse(users=users)
