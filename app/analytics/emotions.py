from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SentimentLabel
from app.repositories import MessageRepository
from app.schemas import EmotionTopicItem, EmotionsAnalyticsResponse

TOPIC_KEYWORDS = {
    "Announcements": ["announce", "notice", "update", "inform", "official", "reminder"],
    "Events": ["event", "meeting", "schedule", "venue", "register", "workshop", "conference"],
    "Elections": ["election", "vote", "candidate", "poll", "ballot", "campaign"],
    "Financial discussions": ["budget", "finance", "payment", "invoice", "cost", "expense", "salary", "fund"],
}


class EmotionsAnalytics:
    @staticmethod
    def classify_topic(text: str) -> str | None:
        lowered = text.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return topic
        return None

    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> EmotionsAnalyticsResponse:
        messages = await MessageRepository(db).get_by_group(group_id)

        topic_data: dict[str, dict] = defaultdict(
            lambda: {"positive": 0, "negative": 0, "total": 0, "senders": set()}
        )

        for msg in messages:
            topic = EmotionsAnalytics.classify_topic(msg.message_text)
            if not topic:
                continue

            data = topic_data[topic]
            data["total"] += 1
            data["senders"].add(msg.sender_name)
            if msg.sentiment == SentimentLabel.POSITIVE:
                data["positive"] += 1
            elif msg.sentiment == SentimentLabel.NEGATIVE:
                data["negative"] += 1

        topics = []
        for topic_name in TOPIC_KEYWORDS:
            data = topic_data.get(topic_name, {"positive": 0, "negative": 0, "total": 0, "senders": set()})
            total = data["total"]
            positive_pct = round((data["positive"] / total * 100) if total else 0, 2)
            negative_pct = round((data["negative"] / total * 100) if total else 0, 2)
            engagement = total * len(data["senders"])
            topics.append(
                EmotionTopicItem(
                    topic=topic_name,
                    positive_pct=positive_pct,
                    negative_pct=negative_pct,
                    engagement_score=engagement,
                )
            )

        return EmotionsAnalyticsResponse(topics=topics)
