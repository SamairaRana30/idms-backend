from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import SentimentLabel, UserRole


class ErrorResponse(BaseModel):
    detail: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    role: UserRole | None = None


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.ANALYST


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_name: str
    uploaded_by: int
    created_at: datetime


class UploadResponse(BaseModel):
    group_id: int
    group_name: str
    message_count: int
    detail: str = "Chat imported successfully"


class UserActivityItem(BaseModel):
    sender_name: str
    message_count: int


class ActivityAnalyticsResponse(BaseModel):
    total_messages: int
    top_10_active_users: list[UserActivityItem]
    bottom_10_active_users: list[UserActivityItem]


class ChartDataResponse(BaseModel):
    labels: list[str]
    values: list[int]


class PeakHourItem(BaseModel):
    hour: int
    message_count: int


class PeakHoursResponse(BaseModel):
    peak_hours: list[PeakHourItem]
    busiest_hour: int


class MediaTypeCount(BaseModel):
    type: str
    count: int
    percentage: float


class MediaComparisonResponse(BaseModel):
    total_messages: int
    breakdown: list[MediaTypeCount]


class SentimentSummaryResponse(BaseModel):
    positive_count: int
    negative_count: int
    neutral_count: int
    timeline: ChartDataResponse


class UserSentimentItem(BaseModel):
    sender_name: str
    positive: int
    negative: int
    neutral: int


class UserSentimentResponse(BaseModel):
    users: list[UserSentimentItem]


class SpamMessageItem(BaseModel):
    id: int
    sender_name: str
    message_text: str
    spam_score: float
    timestamp: datetime


class SuspectedUserItem(BaseModel):
    sender_name: str
    spam_message_count: int
    average_spam_score: float


class SpamAnalyticsResponse(BaseModel):
    spam_messages: list[SpamMessageItem]
    suspected_users: list[SuspectedUserItem]
    threshold: float = 50.0


class InfluentialUserItem(BaseModel):
    sender_name: str
    influence_score: float
    total_messages: int
    rank: int


class InfluentialUsersResponse(BaseModel):
    users: list[InfluentialUserItem]


class NetworkNode(BaseModel):
    id: str
    degree: int


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: int


class NetworkCommunity(BaseModel):
    cluster_id: int
    members: list[str]


class CentralityItem(BaseModel):
    user: str
    score: float


class NetworkAnalyticsResponse(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    density: float
    communities: list[NetworkCommunity]
    centrality: list[CentralityItem]


class EmotionTopicItem(BaseModel):
    topic: str
    positive_pct: float
    negative_pct: float
    engagement_score: int


class EmotionsAnalyticsResponse(BaseModel):
    topics: list[EmotionTopicItem]
