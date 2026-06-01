from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


@notifications_bp.route('', methods=['GET'])
@require_auth
def list_notifications():
    page, limit, offset = paginate(request)
    role = g.user.get('role', 'member')
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT COUNT(*) FROM notifications WHERE target_role = 'all' OR target_role = %s",
            (role,)
        )
        total = cur.fetchone()['count']

        cur.execute(
            """SELECT n.id, n.type, n.title, n.body, n.target_role, n.sent_at,
                      u.full_name AS sent_by_name
               FROM notifications n JOIN users u ON u.id = n.sent_by
               WHERE n.target_role = 'all' OR n.target_role = %s
               ORDER BY n.sent_at DESC LIMIT %s OFFSET %s""",
            (role, limit, offset)
        )
        notifs = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'notifications': notifs, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@notifications_bp.route('', methods=['POST'])
@require_auth
@require_admin
def send_notification():
    data = request.get_json() or {}
    n_type      = data.get('type', 'announcement')
    title       = data.get('title', '').strip()
    body        = data.get('body', '').strip()
    target_role = data.get('target_role', 'all')

    if not title or not body:
        return error('Title and body are required', 400)
    if n_type not in ('announcement', 'reminder', 'broadcast', 'targeted'):
        return error('Invalid notification type', 400)
    if target_role not in ('all', 'admin', 'member'):
        return error('Invalid target_role', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO notifications (type, title, body, sent_by, target_role)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (n_type, title, body, g.user['user_id'], target_role)
        )
        notif_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'notification_id': notif_id}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
