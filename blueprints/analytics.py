import re
from collections import Counter
from datetime import datetime

from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# WhatsApp export line patterns (handles both formats)
_WA_PATTERNS = [
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\]\s*([^:]+):\s*(.+)$'),
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*-\s*([^:]+):\s*(.+)$'),
]
_HOUR_PATTERNS = [
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?\]'),
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}):(\d{2})\s*(AM|PM)?\s*-'),
]
_MEDIA = re.compile(r'<media omitted>|<image omitted>|<video omitted>|<audio omitted>|<document omitted>', re.IGNORECASE)


def _parse_whatsapp(text):
    lines          = text.splitlines()
    messages       = []
    senders        = []
    hours          = []
    text_count     = 0
    media_count    = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        sender = body = None
        for pat in _WA_PATTERNS:
            m = pat.match(line)
            if m:
                sender = m.group(2).strip()
                body   = m.group(3).strip()
                break

        if sender and body:
            messages.append(body)
            senders.append(sender)
            if _MEDIA.search(body):
                media_count += 1
            else:
                text_count += 1

        # Extract hour
        for hpat in _HOUR_PATTERNS:
            hm = hpat.match(line)
            if hm:
                h   = int(hm.group(2))
                ampm = hm.group(4)
                if ampm:
                    if ampm.upper() == 'PM' and h != 12:
                        h += 12
                    elif ampm.upper() == 'AM' and h == 12:
                        h = 0
                hours.append(h)
                break

    total_messages = len(messages)
    active_users   = len(set(senders))
    peak_hour      = Counter(hours).most_common(1)[0][0] if hours else 0

    # Sentiment via VADER on all messages combined
    combined = ' '.join(messages[:500])  # cap for performance
    analyzer = SentimentIntensityAnalyzer()
    vader_score = analyzer.polarity_scores(combined)['compound']

    return {
        'total_messages': total_messages,
        'active_users':   active_users,
        'peak_hour':      peak_hour,
        'sentiment_score': round(vader_score, 4),
        'text_count':     text_count,
        'media_count':    media_count,
    }


@analytics_bp.route('', methods=['GET'])
@require_auth
def list_analytics():
    page, limit, offset = paginate(request)
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) FROM chat_analytics")
        total = cur.fetchone()['count']

        cur.execute(
            """SELECT a.id, a.upload_date, a.total_messages, a.active_users,
                      a.peak_hour, a.sentiment_score, a.text_count, a.media_count,
                      u.full_name AS uploaded_by_name
               FROM chat_analytics a
               LEFT JOIN users u ON u.id::text = a.uploaded_by
               ORDER BY a.upload_date DESC LIMIT %s OFFSET %s""",
            (limit, offset)
        )
        records = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'analytics': records, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@analytics_bp.route('/upload', methods=['POST'])
@require_auth
@require_admin
def upload_analytics():
    if 'file' not in request.files:
        return error('No file provided', 400)

    file = request.files['file']
    if not file.filename.lower().endswith('.txt'):
        return error('Only WhatsApp .txt export files are accepted', 400)

    try:
        text = file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return error(f'Could not read file: {str(e)}', 400)

    stats = _parse_whatsapp(text)

    if stats['total_messages'] == 0:
        return error('No WhatsApp messages found. Make sure this is a WhatsApp chat export (.txt).', 400)

    upload_date = datetime.now().date()

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO chat_analytics "
            "(upload_date, total_messages, active_users, peak_hour, "
            " sentiment_score, text_count, media_count, uploaded_by) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (upload_date, stats['total_messages'], stats['active_users'],
             stats['peak_hour'], stats['sentiment_score'],
             stats['text_count'], stats['media_count'], g.user['user_id'])
        )
        record_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'record_id': record_id, 'stats': stats}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
