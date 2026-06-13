import json
from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.analytics.frequency import FrequencyAnalytics
from app.analytics.influence import InfluenceAnalytics
from app.analytics.peak_hours import PeakHoursAnalytics
from app.models import (
    ActivityReport,
    ChatMessage,
    MessageType,
    SentimentLabel,
    SentimentReport,
    UserStatistics,
    WhatsAppGroup,
)
from app.repositories import GroupRepository, MessageRepository, StatisticsRepository
from app.services.chat_parser import parse_chat_file
from app.utils.file_validation import extract_urls

vader = SentimentIntensityAnalyzer()

PROMOTIONAL_KEYWORDS = ["buy", "offer", "discount", "click here", "sale", "promo", "limited time"]
FORWARD_PATTERNS = ["forwarded", "↪", "fwd:"]


def classify_sentiment(text: str) -> SentimentLabel:
    if not text.strip() or text.lower().startswith(("image omitted", "video omitted", "<media omitted>")):
        return SentimentLabel.NEUTRAL

    vader_score = vader.polarity_scores(text)["compound"]
    blob_score = TextBlob(text).sentiment.polarity
    combined = (vader_score + blob_score) / 2

    if combined > 0.05:
        return SentimentLabel.POSITIVE
    if combined < -0.05:
        return SentimentLabel.NEGATIVE
    return SentimentLabel.NEUTRAL


def calculate_spam_score_for_message(text: str, repeat_count: int) -> float:
    score = 0.0
    lowered = text.lower()

    if len(extract_urls(text)) >= 2:
        score += 25

    if repeat_count >= 3:
        score += 30

    if any(keyword in lowered for keyword in PROMOTIONAL_KEYWORDS):
        score += 25

    if any(pattern in lowered for pattern in FORWARD_PATTERNS):
        score += 20

    return min(score, 100.0)


class UploadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.group_repo = GroupRepository(db)
        self.message_repo = MessageRepository(db)
        self.stats_repo = StatisticsRepository(db)

    async def import_chat(self, content: bytes, group_name: str, uploaded_by: int) -> tuple[WhatsAppGroup, int]:
        parsed = parse_chat_file(content)

        group = WhatsAppGroup(group_name=group_name, uploaded_by=uploaded_by)
        group = await self.group_repo.create(group)

        repeat_tracker: dict[str, Counter] = defaultdict(Counter)
        for msg in parsed:
            repeat_tracker[msg.sender_name][msg.message_text] += 1

        chat_messages: list[ChatMessage] = []
        for msg in parsed:
            sentiment = classify_sentiment(msg.message_text)
            spam_score = calculate_spam_score_for_message(
                msg.message_text, repeat_tracker[msg.sender_name][msg.message_text]
            )
            chat_messages.append(
                ChatMessage(
                    group_id=group.id,
                    sender_name=msg.sender_name,
                    message_text=msg.message_text,
                    message_type=msg.message_type,
                    timestamp=msg.timestamp,
                    sentiment=sentiment,
                    spam_score=spam_score,
                )
            )

        await self.message_repo.bulk_create(chat_messages)
        await self._post_process(group.id, chat_messages)
        return group, len(chat_messages)

    async def _post_process(self, group_id: int, messages: list[ChatMessage]) -> None:
        user_stats: dict[str, dict] = defaultdict(
            lambda: {"total": 0, "media": 0, "text": 0}
        )
        for msg in messages:
            stats = user_stats[msg.sender_name]
            stats["total"] += 1
            if msg.message_type == MessageType.TEXT:
                stats["text"] += 1
            else:
                stats["media"] += 1

        influence_scores = InfluenceAnalytics.compute_scores(messages)
        stat_rows = [
            UserStatistics(
                group_id=group_id,
                sender_name=sender,
                total_messages=data["total"],
                media_messages=data["media"],
                text_messages=data["text"],
                influence_score=influence_scores.get(sender, 0.0),
            )
            for sender, data in user_stats.items()
        ]
        await self.stats_repo.bulk_create_user_stats(stat_rows)

        sentiment_counts = Counter(msg.sentiment for msg in messages if msg.sentiment)
        await self.stats_repo.create_sentiment_report(
            SentimentReport(
                group_id=group_id,
                positive_count=sentiment_counts.get(SentimentLabel.POSITIVE, 0),
                negative_count=sentiment_counts.get(SentimentLabel.NEGATIVE, 0),
                neutral_count=sentiment_counts.get(SentimentLabel.NEUTRAL, 0),
            )
        )

        daily = FrequencyAnalytics.daily_from_messages(messages)
        weekly = FrequencyAnalytics.weekly_from_messages(messages)
        monthly = FrequencyAnalytics.monthly_from_messages(messages)
        peak = PeakHoursAnalytics.from_messages(messages)

        await self.stats_repo.create_activity_report(
            ActivityReport(
                group_id=group_id,
                daily_activity=json.dumps(daily),
                weekly_activity=json.dumps(weekly),
                monthly_activity=json.dumps(monthly),
                peak_hour=peak.busiest_hour,
            )
        )
