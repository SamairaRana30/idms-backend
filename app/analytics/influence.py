import re
from collections import Counter, defaultdict
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage
from app.repositories import MessageRepository, StatisticsRepository
from app.schemas import InfluentialUserItem, InfluentialUsersResponse


class InfluenceAnalytics:
    @staticmethod
    def compute_scores(messages: list[ChatMessage]) -> dict[str, float]:
        if not messages:
            return {}

        message_counts = Counter(msg.sender_name for msg in messages)
        mentions_received: Counter = Counter()
        replies_received: Counter = Counter()
        initiations: Counter = Counter()

        mention_pattern = re.compile(r"@(\w+)")

        for i, msg in enumerate(messages):
            for mention in mention_pattern.findall(msg.message_text):
                mentions_received[mention] += 1

            if i > 0:
                prev = messages[i - 1]
                delta = msg.timestamp - prev.timestamp
                if prev.sender_name != msg.sender_name and delta <= timedelta(minutes=2):
                    replies_received[prev.sender_name] += 1

            if i == 0 or (msg.timestamp - messages[i - 1].timestamp) >= timedelta(minutes=30):
                initiations[msg.sender_name] += 1

        senders = set(message_counts.keys())
        max_messages = max(message_counts.values()) or 1
        max_mentions = max(mentions_received.values()) if mentions_received else 1
        max_replies = max(replies_received.values()) if replies_received else 1
        max_initiations = max(initiations.values()) if initiations else 1

        scores: dict[str, float] = {}
        for sender in senders:
            msg_score = (message_counts[sender] / max_messages) * 30
            mention_score = (mentions_received.get(sender, 0) / max_mentions) * 25
            reply_score = (replies_received.get(sender, 0) / max_replies) * 25
            init_score = (initiations.get(sender, 0) / max_initiations) * 20
            scores[sender] = round(min(msg_score + mention_score + reply_score + init_score, 100), 2)

        return scores

    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> InfluentialUsersResponse:
        stats = await StatisticsRepository(db).get_by_group(group_id)
        if stats:
            users = [
                InfluentialUserItem(
                    sender_name=s.sender_name,
                    influence_score=s.influence_score,
                    total_messages=s.total_messages,
                    rank=idx + 1,
                )
                for idx, s in enumerate(stats)
            ]
            return InfluentialUsersResponse(users=users)

        messages = await MessageRepository(db).get_by_group(group_id)
        scores = InfluenceAnalytics.compute_scores(messages)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        users = [
            InfluentialUserItem(
                sender_name=name,
                influence_score=score,
                total_messages=sum(1 for m in messages if m.sender_name == name),
                rank=idx + 1,
            )
            for idx, (name, score) in enumerate(ranked)
        ]
        return InfluentialUsersResponse(users=users)
