"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("admin", "analyst", name="userrole"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    op.create_table(
        "whatsapp_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_name", sa.String(length=255), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("message_type", sa.Enum("text", "image", "video", "audio", "document", name="messagetype"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment", sa.Enum("positive", "negative", "neutral", name="sentimentlabel"), nullable=True),
        sa.Column("spam_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["whatsapp_groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_group_id", "chat_messages", ["group_id"], unique=False)
    op.create_index("ix_chat_messages_sender_name", "chat_messages", ["sender_name"], unique=False)
    op.create_index("ix_chat_messages_timestamp", "chat_messages", ["timestamp"], unique=False)

    op.create_table(
        "user_statistics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=False),
        sa.Column("total_messages", sa.Integer(), nullable=False),
        sa.Column("media_messages", sa.Integer(), nullable=False),
        sa.Column("text_messages", sa.Integer(), nullable=False),
        sa.Column("influence_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["whatsapp_groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_statistics_group_id", "user_statistics", ["group_id"], unique=False)
    op.create_index("ix_user_statistics_sender_name", "user_statistics", ["sender_name"], unique=False)

    op.create_table(
        "sentiment_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("positive_count", sa.Integer(), nullable=False),
        sa.Column("negative_count", sa.Integer(), nullable=False),
        sa.Column("neutral_count", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["whatsapp_groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sentiment_reports_group_id", "sentiment_reports", ["group_id"], unique=False)

    op.create_table(
        "activity_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("daily_activity", sa.Text(), nullable=False),
        sa.Column("weekly_activity", sa.Text(), nullable=False),
        sa.Column("monthly_activity", sa.Text(), nullable=False),
        sa.Column("peak_hour", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["whatsapp_groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_reports_group_id", "activity_reports", ["group_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_activity_reports_group_id", table_name="activity_reports")
    op.drop_table("activity_reports")
    op.drop_index("ix_sentiment_reports_group_id", table_name="sentiment_reports")
    op.drop_table("sentiment_reports")
    op.drop_index("ix_user_statistics_sender_name", table_name="user_statistics")
    op.drop_index("ix_user_statistics_group_id", table_name="user_statistics")
    op.drop_table("user_statistics")
    op.drop_index("ix_chat_messages_timestamp", table_name="chat_messages")
    op.drop_index("ix_chat_messages_sender_name", table_name="chat_messages")
    op.drop_index("ix_chat_messages_group_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_table("whatsapp_groups")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
