from datetime import UTC, datetime

import pytest

from app.analytics.activity import ActivityAnalytics
from app.analytics.frequency import FrequencyAnalytics
from app.analytics.influence import InfluenceAnalytics
from app.analytics.media import MediaAnalytics
from app.analytics.network import NetworkAnalytics
from app.analytics.peak_hours import PeakHoursAnalytics
from app.analytics.sentiment import SentimentAnalytics
from app.analytics.spam import SpamAnalytics
from app.models import ChatMessage, MessageType, SentimentLabel, UserStatistics, WhatsAppGroup
from app.services.upload_service import calculate_spam_score_for_message, classify_sentiment


def _msg(sender, text, hour=10, msg_type=MessageType.TEXT, sentiment=None, spam=0.0, msg_id=1):
    return ChatMessage(
        id=msg_id,
        group_id=1,
        sender_name=sender,
        message_text=text,
        message_type=msg_type,
        timestamp=datetime(2025, 6, 1, hour, 0, 0, tzinfo=UTC),
        sentiment=sentiment,
        spam_score=spam,
    )


@pytest.mark.asyncio
async def test_activity(db_session):
    for i, sender in enumerate(["Alice", "Alice", "Bob"]):
        db_session.add(_msg(sender, f"msg {i}", msg_id=i + 1))
    await db_session.flush()
    result = await ActivityAnalytics.analyze(db_session, 1)
    assert result.total_messages == 3
    assert result.top_10_active_users[0].sender_name == "Alice"


@pytest.mark.asyncio
async def test_frequency(db_session):
    db_session.add(_msg("A", "hi", hour=8, msg_id=1))
    db_session.add(_msg("B", "hey", hour=14, msg_id=2))
    await db_session.flush()
    daily = await FrequencyAnalytics.daily(db_session, 1)
    weekly = await FrequencyAnalytics.weekly(db_session, 1)
    monthly = await FrequencyAnalytics.monthly(db_session, 1)
    assert len(daily.labels) >= 1
    assert len(weekly.labels) >= 1
    assert len(monthly.labels) >= 1


@pytest.mark.asyncio
async def test_peak_hours(db_session):
    db_session.add(_msg("A", "morning", hour=9, msg_id=1))
    db_session.add(_msg("B", "morning2", hour=9, msg_id=2))
    await db_session.flush()
    result = await PeakHoursAnalytics.analyze(db_session, 1)
    assert result.peak_hours[9].message_count == 2


@pytest.mark.asyncio
async def test_media(db_session):
    db_session.add(_msg("A", "text", msg_type=MessageType.TEXT, msg_id=1))
    db_session.add(_msg("B", "image omitted", msg_type=MessageType.IMAGE, msg_id=2))
    await db_session.flush()
    result = await MediaAnalytics.analyze(db_session, 1)
    assert result.total_messages == 2


@pytest.mark.asyncio
async def test_sentiment(db_session):
    db_session.add(_msg("A", "great", sentiment=SentimentLabel.POSITIVE, msg_id=1))
    db_session.add(_msg("B", "bad", sentiment=SentimentLabel.NEGATIVE, msg_id=2))
    await db_session.flush()
    summary = await SentimentAnalytics.analyze(db_session, 1)
    users = await SentimentAnalytics.by_users(db_session, 1)
    assert summary.positive_count == 1
    assert len(users.users) == 2


@pytest.mark.asyncio
async def test_spam(db_session):
    db_session.add(_msg("Spammer", "spam", spam=75.0, msg_id=1))
    await db_session.flush()
    result = await SpamAnalytics.analyze(db_session, 1)
    assert len(result.spam_messages) == 1


@pytest.mark.asyncio
async def test_influence_from_stats(db_session):
    db_session.add(UserStatistics(group_id=1, sender_name="Alice", total_messages=10, media_messages=2, text_messages=8, influence_score=80.0))
    await db_session.flush()
    result = await InfluenceAnalytics.analyze(db_session, 1)
    assert result.users[0].sender_name == "Alice"


@pytest.mark.asyncio
async def test_network(db_session):
    db_session.add(_msg("Alice", "hello", hour=10, msg_id=1))
    db_session.add(_msg("Bob", "reply", hour=10, msg_id=2))
    await db_session.flush()
    result = await NetworkAnalytics.analyze(db_session, 1)
    assert len(result.nodes) >= 2


def test_classify_sentiment_neutral():
    assert classify_sentiment("image omitted") == SentimentLabel.NEUTRAL


def test_spam_score_repeat():
    score = calculate_spam_score_for_message("hello", 5)
    assert score >= 30
