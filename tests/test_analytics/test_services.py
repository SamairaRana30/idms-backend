from datetime import UTC, datetime

import pytest

from app.analytics.activity import ActivityAnalytics
from app.analytics.emotions import EmotionsAnalytics
from app.analytics.influence import InfluenceAnalytics
from app.analytics.spam import SpamAnalytics
from app.models import ChatMessage, MessageType, SentimentLabel
from app.services.upload_service import calculate_spam_score_for_message, classify_sentiment


def _make_message(sender: str, text: str, hour: int = 10, sentiment=None, spam_score=0.0):
    return ChatMessage(
        id=1,
        group_id=1,
        sender_name=sender,
        message_text=text,
        message_type=MessageType.TEXT,
        timestamp=datetime(2025, 6, 1, hour, 0, 0, tzinfo=UTC),
        sentiment=sentiment,
        spam_score=spam_score,
    )


@pytest.mark.asyncio
async def test_classify_sentiment_positive():
    result = classify_sentiment("I love this amazing wonderful news!")
    assert result == SentimentLabel.POSITIVE


@pytest.mark.asyncio
async def test_classify_sentiment_negative():
    result = classify_sentiment("I hate this terrible awful situation.")
    assert result == SentimentLabel.NEGATIVE


def test_spam_score_high_for_links_and_promo():
    score = calculate_spam_score_for_message(
        "Buy now discount click here https://a.com https://b.com", 1
    )
    assert score >= 50


def test_influence_scores():
    messages = [
        _make_message("Alice", "Hello everyone"),
        _make_message("Bob", "@Alice thanks"),
        _make_message("Alice", "Welcome @Bob"),
    ]
    scores = InfluenceAnalytics.compute_scores(messages)
    assert "Alice" in scores
    assert scores["Alice"] > 0


@pytest.mark.asyncio
async def test_emotions_topic_classification(db_session):
    messages = [
        _make_message("Alice", "Official announcement about meeting", sentiment=SentimentLabel.POSITIVE),
        _make_message("Bob", "Great event schedule for workshop", sentiment=SentimentLabel.POSITIVE),
        _make_message("Charlie", "Vote in the election poll", sentiment=SentimentLabel.NEUTRAL),
        _make_message("Diana", "Budget finance payment invoice", sentiment=SentimentLabel.NEGATIVE),
    ]
    for i, msg in enumerate(messages):
        msg.id = i + 1
        db_session.add(msg)
    await db_session.flush()

    result = await EmotionsAnalytics.analyze(db_session, 1)
    assert len(result.topics) == 4
