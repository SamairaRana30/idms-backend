import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from config import Config
from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


@notifications_bp.route('', methods=['GET'])
@require_auth
def list_notifications():
    page, limit, offset = paginate(request)
    role    = g.user.get('role', 'member')
    is_admin = role == 'admin'
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        if is_admin:
            cur.execute("SELECT COUNT(*) FROM notifications")
            total = cur.fetchone()['count']
            cur.execute(
                """SELECT n.id, n.type, n.title, n.body, n.target_role, n.sent_at,
                          u.full_name AS sent_by_name
                   FROM notifications n
                   LEFT JOIN users u ON u.id::text = n.sent_by
                   ORDER BY n.sent_at DESC LIMIT %s OFFSET %s""",
                (limit, offset)
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM notifications WHERE target_role IN ('all',%s)",
                (role,)
            )
            total = cur.fetchone()['count']
            cur.execute(
                """SELECT n.id, n.type, n.title, n.body, n.target_role, n.sent_at,
                          u.full_name AS sent_by_name
                   FROM notifications n
                   LEFT JOIN users u ON u.id::text = n.sent_by
                   WHERE n.target_role IN ('all',%s)
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
@notifications_bp.route('/announce', methods=['POST'])
@require_auth
@require_admin
def send_notification():
    data        = request.get_json() or {}
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
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        # Save to DB
        cur.execute(
            "INSERT INTO notifications (type, title, body, sent_by, target_role) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (n_type, title, body, g.user['user_id'], target_role)
        )
        notif_id = str(cur.fetchone()[0])

        # Get matching members for email
        if target_role == 'all':
            cur.execute("SELECT email, full_name FROM users WHERE is_active = true")
        else:
            cur.execute(
                "SELECT email, full_name FROM users WHERE is_active = true AND role = %s",
                (target_role,)
            )
        members = cur.fetchall()
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)

    sent_to = len(members)

    # Send emails if SMTP configured
    if Config.SMTP_USER and Config.SMTP_PASS:
        sent = 0
        for m in members:
            try:
                msg = MIMEMultipart()
                msg['From']    = Config.SMTP_FROM or Config.SMTP_USER
                msg['To']      = m['email']
                msg['Subject'] = f"[IDMS] {title}"
                msg.attach(MIMEText(f"Dear {m['full_name'] or 'Member'},\n\n{body}\n\nIDMS System", 'plain'))
                with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as srv:
                    srv.starttls()
                    srv.login(Config.SMTP_USER, Config.SMTP_PASS)
                    srv.send_message(msg)
                sent += 1
            except Exception:
                pass
        sent_to = sent

    return success({'notification_id': notif_id, 'saved': True, 'sent_to': sent_to}, 201)
