from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import token_required, admin_required
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')


@analytics_bp.route('', methods=['GET'])
@token_required
def list_analytics():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT a.id, a.upload_date, a.total_messages, a.active_users,
                      a.peak_hour, a.sentiment_score, a.text_count, a.media_count, a.uploaded_by,
                      u.full_name AS uploaded_by_name
               FROM chat_analytics a JOIN users u ON u.id = a.uploaded_by
               ORDER BY a.upload_date DESC"""
        )
        records = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'analytics': records})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@analytics_bp.route('', methods=['POST'])
@token_required
@admin_required
def upload_analytics():
    data = request.get_json() or {}
    required = ['upload_date', 'total_messages', 'active_users',
                'peak_hour', 'sentiment_score', 'text_count', 'media_count']
    missing = [f for f in required if f not in data]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chat_analytics
               (upload_date, total_messages, active_users, peak_hour,
                sentiment_score, text_count, media_count, uploaded_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (data['upload_date'], data['total_messages'], data['active_users'],
             data['peak_hour'], data['sentiment_score'], data['text_count'],
             data['media_count'], g.user['user_id'])
        )
        record_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'record_id': record_id}, message='Analytics uploaded', status=201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
