from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.analytics.activity import ActivityAnalytics
from app.analytics.emotions import EmotionsAnalytics
from app.analytics.frequency import FrequencyAnalytics
from app.analytics.influence import InfluenceAnalytics
from app.analytics.media import MediaAnalytics
from app.analytics.network import NetworkAnalytics
from app.analytics.peak_hours import PeakHoursAnalytics
from app.analytics.sentiment import SentimentAnalytics
from app.analytics.spam import SpamAnalytics
from app.api.deps import get_group_or_404, require_analyst
from app.database.session import get_db
from app.models import User
from app.schemas import (
    ActivityAnalyticsResponse,
    ChartDataResponse,
    EmotionsAnalyticsResponse,
    ErrorResponse,
    InfluentialUsersResponse,
    MediaComparisonResponse,
    NetworkAnalyticsResponse,
    PeakHoursResponse,
    SentimentSummaryResponse,
    SpamAnalyticsResponse,
    UserSentimentResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/activity",
    response_model=ActivityAnalyticsResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get messaging activity analytics",
)
async def activity_analytics(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await ActivityAnalytics.analyze(db, group_id)


@router.get(
    "/frequency/daily",
    response_model=ChartDataResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get daily message frequency",
)
async def daily_frequency(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await FrequencyAnalytics.daily(db, group_id)


@router.get(
    "/frequency/weekly",
    response_model=ChartDataResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get weekly message frequency",
)
async def weekly_frequency(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await FrequencyAnalytics.weekly(db, group_id)


@router.get(
    "/frequency/monthly",
    response_model=ChartDataResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get monthly message frequency",
)
async def monthly_frequency(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await FrequencyAnalytics.monthly(db, group_id)


@router.get(
    "/peak-hours",
    response_model=PeakHoursResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get peak chat hours analysis",
)
async def peak_hours(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await PeakHoursAnalytics.analyze(db, group_id)


@router.get(
    "/media-comparison",
    response_model=MediaComparisonResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get text vs media message comparison",
)
async def media_comparison(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await MediaAnalytics.analyze(db, group_id)


@router.get(
    "/sentiment",
    response_model=SentimentSummaryResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get group sentiment analysis summary",
)
async def sentiment_summary(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await SentimentAnalytics.analyze(db, group_id)


@router.get(
    "/sentiment/users",
    response_model=UserSentimentResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get per-user sentiment breakdown",
)
async def sentiment_by_users(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await SentimentAnalytics.by_users(db, group_id)


@router.get(
    "/spam",
    response_model=SpamAnalyticsResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get spam detection analytics",
)
async def spam_analytics(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await SpamAnalytics.analyze(db, group_id)


@router.get(
    "/influential-users",
    response_model=InfluentialUsersResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get influential user rankings",
)
async def influential_users(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await InfluenceAnalytics.analyze(db, group_id)


@router.get(
    "/network",
    response_model=NetworkAnalyticsResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get interaction network analysis",
)
async def network_analytics(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await NetworkAnalytics.analyze(db, group_id)


@router.get(
    "/emotions",
    response_model=EmotionsAnalyticsResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get emotional reaction analysis by topic",
)
async def emotions_analytics(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    await get_group_or_404(group_id, db)
    return await EmotionsAnalytics.analyze(db, group_id)
