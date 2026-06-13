import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def _enum_column(enum_class: type[enum.Enum]) -> Enum:
    return Enum(
        enum_class,
        values_callable=lambda choices: [item.value for item in choices],
    )


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(_enum_column(UserRole), nullable=False, default=UserRole.ANALYST)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    groups: Mapped[list["WhatsAppGroup"]] = relationship(back_populates="uploader")


class WhatsAppGroup(Base):
    __tablename__ = "whatsapp_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uploader: Mapped["User"] = relationship(back_populates="groups")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    user_statistics: Mapped[list["UserStatistics"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    sentiment_reports: Mapped[list["SentimentReport"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    activity_reports: Mapped[list["ActivityReport"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_groups.id"), nullable=False, index=True)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message_type: Mapped[MessageType] = mapped_column(_enum_column(MessageType), nullable=False, default=MessageType.TEXT)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sentiment: Mapped[SentimentLabel | None] = mapped_column(_enum_column(SentimentLabel), nullable=True)
    spam_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    group: Mapped["WhatsAppGroup"] = relationship(back_populates="messages")


class UserStatistics(Base):
    __tablename__ = "user_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_groups.id"), nullable=False, index=True)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    total_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    media_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    influence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    group: Mapped["WhatsAppGroup"] = relationship(back_populates="user_statistics")


class SentimentReport(Base):
    __tablename__ = "sentiment_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_groups.id"), nullable=False, index=True)
    positive_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["WhatsAppGroup"] = relationship(back_populates="sentiment_reports")


class ActivityReport(Base):
    __tablename__ = "activity_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_groups.id"), nullable=False, index=True)
    daily_activity: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    weekly_activity: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    monthly_activity: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    peak_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["WhatsAppGroup"] = relationship(back_populates="activity_reports")
