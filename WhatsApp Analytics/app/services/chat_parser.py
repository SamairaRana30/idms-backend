import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.models import MessageType
from app.utils.datetime_helpers import ensure_utc


class ExportFormat(str, Enum):
    ANDROID = "android"
    IPHONE = "iphone"


ANDROID_PATTERN = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}:\d{2})\] ([^:]+): (.*)$"
)
IPHONE_PATTERN = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}:\d{2} [AP]M)\] ([^:]+): (.*)$"
)

MEDIA_PATTERNS = {
    MessageType.IMAGE: [
        r"image omitted",
        r"<Media omitted>",
        r"\.jpg",
        r"\.jpeg",
        r"\.png",
        r"\.gif",
        r"\.webp",
    ],
    MessageType.VIDEO: [
        r"video omitted",
        r"\.mp4",
        r"\.mov",
        r"\.avi",
    ],
    MessageType.AUDIO: [
        r"audio omitted",
        r"\.mp3",
        r"\.ogg",
        r"\.wav",
        r"\.opus",
        r"PTT",
    ],
    MessageType.DOCUMENT: [
        r"document omitted",
        r"\(file attached\)",
        r"\.pdf",
        r"\.doc",
        r"\.docx",
        r"\.xlsx",
        r"\.ppt",
    ],
}


@dataclass
class ParsedMessage:
    sender_name: str
    message_text: str
    message_type: MessageType
    timestamp: datetime


class ChatParserError(Exception):
    pass


def _parse_timestamp(date_str: str, time_str: str) -> datetime:
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        "%d/%m/%Y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%d/%m/%y %I:%M:%S %p",
        "%m/%d/%y %I:%M:%S %p",
    ):
        try:
            return ensure_utc(datetime.strptime(f"{date_str} {time_str}", fmt))
        except ValueError:
            continue
    raise ChatParserError(f"Unable to parse timestamp: {date_str} {time_str}")


def detect_message_type(text: str) -> MessageType:
    lowered = text.lower()
    for msg_type, patterns in MEDIA_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lowered, re.IGNORECASE):
                return msg_type
    return MessageType.TEXT


def detect_format(content: str) -> ExportFormat:
    for line in content.splitlines()[:20]:
        line = line.strip()
        if not line:
            continue
        if IPHONE_PATTERN.match(line):
            return ExportFormat.IPHONE
        if ANDROID_PATTERN.match(line):
            return ExportFormat.ANDROID
    raise ChatParserError("Unable to detect WhatsApp export format")


def parse_chat_content(content: str, min_messages: int = 1) -> list[ParsedMessage]:
    if not content.strip():
        raise ChatParserError("Chat file is empty")

    export_format = detect_format(content)
    pattern = IPHONE_PATTERN if export_format == ExportFormat.IPHONE else ANDROID_PATTERN

    messages: list[ParsedMessage] = []
    current: ParsedMessage | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip("\ufeff").rstrip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            if current:
                messages.append(current)
            date_str, time_str, sender, text = match.groups()
            current = ParsedMessage(
                sender_name=sender.strip(),
                message_text=text.strip(),
                message_type=detect_message_type(text),
                timestamp=_parse_timestamp(date_str, time_str),
            )
        elif current:
            current.message_text = f"{current.message_text}\n{line}".strip()
            current.message_type = detect_message_type(current.message_text)

    if current:
        messages.append(current)

    if len(messages) < min_messages:
        raise ChatParserError(f"Chat must contain at least {min_messages} valid message(s)")

    return messages


def parse_chat_file(content: bytes) -> list[ParsedMessage]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("utf-8-sig", errors="replace")
    return parse_chat_content(text)
