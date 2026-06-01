import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

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
_MEDIA        = re.compile(r'<media omitted>|<image omitted>|<video omitted>|<audio omitted>', re.IGNORECASE)
_URL          = re.compile(r'https?://\S+')
_SPAM_KEYWORDS = {'free','win','winner','click here','discount','offer','limited','urgent','prize','congratulations','selected','voucher','claim'}


def _to_minutes(h, m):
    return h * 60 + m


def _parse_whatsapp(text):
    vader    = SentimentIntensityAnalyzer()
    messages = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pat in _WA_PATTERNS:
            m = pat.match(line)
            if m:
                date_str        = m.group(1)
                h_raw, min_raw  = int(m.group(2)), int(m.group(3))
                ampm            = m.group(4)
                sender          = m.group(5).strip()
                body            = m.group(6).strip()

                if ampm:
                    if ampm.upper() == 'PM' and h_raw != 12:
                        h_raw += 12
                    elif ampm.upper() == 'AM' and h_raw == 12:
                        h_raw = 0

                is_media = bool(_MEDIA.search(body))
                messages.append({
                    'date':     date_str,
                    'hour':     h_raw,
                    'minute':   min_raw,
                    'mins':     _to_minutes(h_raw, min_raw),
                    'sender':   sender,
                    'body':     body,
                    'is_media': is_media,
                })
                break

    if not messages:
        return None

    senders_list  = [m['sender'] for m in messages]
    text_msgs     = [m for m in messages if not m['is_media']]
    media_msgs    = [m for m in messages if m['is_media']]
    total         = len(messages)
    active_users  = len(set(senders_list))
    hours_list    = [m['hour'] for m in messages]
    peak_hour     = Counter(hours_list).most_common(1)[0][0] if hours_list else 0

    # ── Sentiment ─────────────────────────────────────────────────────────────
    combined        = ' '.join(m['body'] for m in text_msgs[:500])
    sentiment_score = round(vader.polarity_scores(combined)['compound'], 4)

    # ── Hourly distribution ───────────────────────────────────────────────────
    hourly_data = {str(h): hours_list.count(h) for h in range(24)}

    # ── Daily distribution ────────────────────────────────────────────────────
    daily_counter = defaultdict(int)
    for m in messages:
        daily_counter[m['date']] += 1
    daily_data = [{'date': d, 'count': c} for d, c in sorted(daily_counter.items())]

    # ── Top senders ───────────────────────────────────────────────────────────
    sender_counts = Counter(senders_list)
    top_senders   = [{'name': s, 'count': c} for s, c in sender_counts.most_common(10)]

    # ── Spam detection ────────────────────────────────────────────────────────
    spam_list = []
    for m in text_msgs:
        body_lower = m['body'].lower()
        reason     = None
        alpha_chars = [c for c in m['body'] if c.isalpha()]
        if len(alpha_chars) >= 10 and sum(c.isupper() for c in alpha_chars) / len(alpha_chars) > 0.7:
            reason = 'ALL CAPS'
        elif any(kw in body_lower for kw in _SPAM_KEYWORDS):
            reason = 'Promotional keyword'
        elif len(_URL.findall(m['body'])) >= 2:
            reason = 'Repeated URLs'
        if reason:
            spam_list.append({'sender': m['sender'], 'body': m['body'][:200], 'reason': reason})
    spam_count = len(spam_list)

    # ── Emotional highlights (per-message VADER) ──────────────────────────────
    scored_msgs = []
    for m in text_msgs[:1000]:
        s = vader.polarity_scores(m['body'])['compound']
        scored_msgs.append({'sender': m['sender'], 'body': m['body'][:200], 'score': round(s, 3)})

    most_positive = sorted(scored_msgs, key=lambda x: x['score'], reverse=True)[:5]
    most_negative = sorted(scored_msgs, key=lambda x: x['score'])[:5]
    emotional_highlights = {'most_positive': most_positive, 'most_negative': most_negative}

    # ── Influential members (5-minute reply window) ───────────────────────────
    influence = Counter()
    for i in range(1, len(messages)):
        curr = messages[i]
        prev = messages[i - 1]
        if curr['sender'] != prev['sender']:
            time_diff = curr['mins'] - prev['mins']
            if 0 <= time_diff <= 5:
                influence[prev['sender']] += 1

    influential_members = [
        {'rank': i + 1, 'sender': s, 'influence_score': c}
        for i, (s, c) in enumerate(influence.most_common(10))
    ]

    # ── Interaction clusters (reply pairs) ────────────────────────────────────
    pair_counts = Counter()
    for i in range(1, len(messages)):
        curr = messages[i]
        prev = messages[i - 1]
        if curr['sender'] != prev['sender']:
            pair_counts[f"{prev['sender']} → {curr['sender']}"] += 1

    interaction_clusters = [
        {'pair': p, 'count': c}
        for p, c in pair_counts.most_common(10)
    ]

    return {
        'total_messages':     total,
        'active_users':       active_users,
        'peak_hour':          peak_hour,
        'sentiment_score':    sentiment_score,
        'text_count':         len(text_msgs),
        'media_count':        len(media_msgs),
        'hourly_data':        hourly_data,
        'daily_data':         daily_data,
        'top_senders':        top_senders,
        'spam_count':         spam_count,
        'spam_messages':      spam_list[:20],
        'emotional_highlights': emotional_highlights,
        'influential_members': influential_members,
        'interaction_clusters': interaction_clusters,
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
    if not stats or stats['total_messages'] == 0:
        return error('No WhatsApp messages found. Ensure this is a WhatsApp chat export (.txt).', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            """INSERT INTO chat_analytics
               (upload_date, total_messages, active_users, peak_hour,
                sentiment_score, text_count, media_count, uploaded_by,
                hourly_data, top_senders, daily_data,
                spam_count, spam_messages,
                emotional_highlights, influential_members, interaction_clusters)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING id""",
            (datetime.now().date(),
             stats['total_messages'], stats['active_users'], stats['peak_hour'],
             stats['sentiment_score'], stats['text_count'], stats['media_count'],
             g.user['user_id'],
             json.dumps(stats['hourly_data']),
             json.dumps(stats['top_senders']),
             json.dumps(stats['daily_data']),
             stats['spam_count'],
             json.dumps(stats['spam_messages']),
             json.dumps(stats['emotional_highlights']),
             json.dumps(stats['influential_members']),
             json.dumps(stats['interaction_clusters']))
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
                      a.spam_count, u.full_name AS uploaded_by_name
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


@analytics_bp.route('/<record_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_analytics(record_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM chat_analytics WHERE id = %s", (record_id,))
        conn.commit()
        return success({'message': 'Record deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@analytics_bp.route('', methods=['GET'])
@require_auth
def list_analytics():
    return get_history()
