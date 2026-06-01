import json
import re
from collections import Counter
from datetime import datetime

from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

_WA_PATTERNS = [
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?\]\s*([^:]+):\s*(.+)$'),
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}):(\d{2})\s*(AM|PM)?\s*-\s*([^:]+):\s*(.+)$'),
]
_MEDIA = re.compile(r'<media omitted>|<image omitted>|<video omitted>|<audio omitted>', re.IGNORECASE)


def _parse_whatsapp(text):
    messages = []
    senders  = []
    hours    = []
    text_count = media_count = 0

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pat in _WA_PATTERNS:
            m = pat.match(line)
            if m:
                h_raw, ampm = int(m.group(2)), m.group(4)
                if ampm:
                    if ampm.upper() == 'PM' and h_raw != 12:
                        h_raw += 12
                    elif ampm.upper() == 'AM' and h_raw == 12:
                        h_raw = 0
                sender = m.group(5).strip()
                body   = m.group(6).strip()
                senders.append(sender)
                hours.append(h_raw)
                messages.append(body)
                if _MEDIA.search(body):
                    media_count += 1
                else:
                    text_count += 1
                break

    total_messages = len(messages)
    active_users   = len(set(senders))
    peak_hour      = Counter(hours).most_common(1)[0][0] if hours else 0

    combined = ' '.join(messages[:500])
    vader    = SentimentIntensityAnalyzer()
    sentiment_score = round(vader.polarity_scores(combined)['compound'], 4)

    hourly_data = {str(h): hours.count(h) for h in range(24)}
    top_senders = [{'name': s, 'count': c}
                   for s, c in Counter(senders).most_common(10)]

    return {
        'total_messages':  total_messages,
        'active_users':    active_users,
        'peak_hour':       peak_hour,
        'sentiment_score': sentiment_score,
        'text_count':      text_count,
        'media_count':     media_count,
        'hourly_data':     hourly_data,
        'top_senders':     top_senders,
    }


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
        return error('No WhatsApp messages found. Ensure this is a WhatsApp chat export (.txt).', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO chat_analytics "
            "(upload_date, total_messages, active_users, peak_hour, "
            " sentiment_score, text_count, media_count, uploaded_by, "
            " hourly_data, top_senders) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (datetime.now().date(),
             stats['total_messages'], stats['active_users'], stats['peak_hour'],
             stats['sentiment_score'], stats['text_count'], stats['media_count'],
             g.user['user_id'],
             json.dumps(stats['hourly_data']),
             json.dumps(stats['top_senders']))
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


@analytics_bp.route('/latest', methods=['GET'])
@require_auth
def get_latest():
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT a.*, u.full_name AS uploaded_by_name
               FROM chat_analytics a
               LEFT JOIN users u ON u.id::text = a.uploaded_by
               ORDER BY a.upload_date DESC LIMIT 1"""
        )
        row = cur.fetchone()
        if not row:
            return error('No analytics uploaded yet', 404)
        return success({'analytics': dict(row) | {'id': str(row['id'])}})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@analytics_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
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


@analytics_bp.route('', methods=['GET'])
@require_auth
def list_analytics():
    return get_history()
