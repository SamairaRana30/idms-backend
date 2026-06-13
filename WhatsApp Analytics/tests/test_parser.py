import os

import pytest

from app.services.chat_parser import ChatParserError, detect_message_type, parse_chat_content, parse_chat_file
from app.models import MessageType


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


def test_parse_android_format():
    path = os.path.join(SAMPLE_DIR, "sample_android_chat.txt")
    with open(path, "rb") as f:
        messages = parse_chat_file(f.read())
    assert len(messages) > 50
    assert messages[0].sender_name == "Alice"


def test_parse_iphone_format():
    path = os.path.join(SAMPLE_DIR, "sample_iphone_chat.txt")
    with open(path, "rb") as f:
        messages = parse_chat_file(f.read())
    assert len(messages) > 30
    assert messages[0].sender_name == "Alice"


def test_detect_media_image():
    assert detect_message_type("image omitted") == MessageType.IMAGE


def test_detect_media_video():
    assert detect_message_type("video omitted") == MessageType.VIDEO


def test_detect_media_document():
    assert detect_message_type("(file attached)") == MessageType.DOCUMENT


def test_multiline_message():
    content = """[01/06/2025, 08:00:00] Alice: Line one
continued line two
[01/06/2025, 08:01:00] Bob: Next message"""
    messages = parse_chat_content(content)
    assert len(messages) == 2
    assert "continued line two" in messages[0].message_text


def test_empty_file_raises():
    with pytest.raises(ChatParserError):
        parse_chat_content("")


def test_invalid_format_raises():
    with pytest.raises(ChatParserError):
        parse_chat_content("This is not a valid whatsapp export\nRandom text only")
