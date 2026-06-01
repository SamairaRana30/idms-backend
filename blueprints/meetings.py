import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from config import Config
from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate
from utils.audit import log_action

meetings_bp = Blueprint('meetings', __name__, url_prefix='/api/v1/meetings')


@meetings_bp.route('', methods=['GET'])
@require_auth
def list_meetings():
    page, limit, offset = paginate(request)
    status_filter = request.args.get('status', '').strip()
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        where = "WHERE m.status = %s" if status_filter else ""
        params_count = [status_filter] if status_filter else []

        cur.execute(f"SELECT COUNT(*) FROM meetings m {where}", params_count)
        total = cur.fetchone()['count']

        cur.execute(
            f"""SELECT m.id, m.title, m.scheduled_at, m.location, m.agenda,
                       m.minutes, m.status, m.created_at,
                       u.full_name AS created_by_name
                FROM meetings m
                LEFT JOIN users u ON u.id::text = m.created_by::text
                {where}
                ORDER BY m.scheduled_at DESC LIMIT %s OFFSET %s""",
            [*params_count, limit, offset]
        )
        meetings = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'meetings': meetings, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('/<meeting_id>', methods=['GET'])
@require_auth
def get_meeting(meeting_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT m.*, u.full_name AS created_by_name
               FROM meetings m
               LEFT JOIN users u ON u.id::text = m.created_by::text
               WHERE m.id = %s""",
            (meeting_id,)
        )
        meeting = cur.fetchone()
        if not meeting:
            return error('Meeting not found', 404)
        return success({'meeting': dict(meeting) | {'id': str(meeting['id'])}})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('', methods=['POST'])
@require_auth
@require_admin
def create_meeting():
    data         = request.get_json() or {}
    title        = data.get('title', '').strip()
    scheduled_at = data.get('scheduled_at')
    location     = data.get('location', '')
    agenda       = data.get('agenda', '')

    if not title or not scheduled_at:
        return error('Title and scheduled_at are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO meetings (title, scheduled_at, location, agenda, created_by) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (title, scheduled_at, location, agenda, g.user['user_id'])
        )
        meeting_id = str(cur.fetchone()[0])
        conn.commit()
        log_action('meeting.create', 'meeting', meeting_id, g.user['user_id'], {'title': title})
        return success({'meeting_id': meeting_id}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('/<meeting_id>/minutes', methods=['PUT'])
@require_auth
@require_admin
def save_minutes(meeting_id):
    data    = request.get_json() or {}
    minutes = data.get('minutes', '')
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE meetings SET minutes = %s WHERE id = %s RETURNING id",
            (minutes, meeting_id)
        )
        if not cur.fetchone():
            conn.rollback()
            return error('Meeting not found', 404)
        conn.commit()
        log_action('meeting.minutes', 'meeting', meeting_id, g.user['user_id'])
        return success({'message': 'Minutes saved'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('/<meeting_id>/complete', methods=['PUT'])
@require_auth
@require_admin
def complete_meeting(meeting_id):
    return _set_meeting_status(meeting_id, 'completed')


@meetings_bp.route('/<meeting_id>/archive', methods=['PUT'])
@require_auth
@require_admin
def archive_meeting(meeting_id):
    return _set_meeting_status(meeting_id, 'archived')


def _set_meeting_status(meeting_id, status):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE meetings SET status = %s WHERE id = %s RETURNING id",
            (status, meeting_id)
        )
        if not cur.fetchone():
            conn.rollback()
            return error('Meeting not found', 404)
        conn.commit()
        log_action(f'meeting.{status}', 'meeting', meeting_id, g.user['user_id'])
        return success({'message': f'Meeting marked as {status}'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('/<meeting_id>/invite', methods=['POST'])
@require_auth
@require_admin
def send_invitations(meeting_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM meetings WHERE id = %s", (meeting_id,))
        meeting = cur.fetchone()
        if not meeting:
            return error('Meeting not found', 404)

        cur.execute("SELECT email, full_name FROM users WHERE is_active = true")
        members = cur.fetchall()
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)

    if not Config.SMTP_USER or not Config.SMTP_PASS:
        return error(
            'Email not configured. Set SMTP_USER and SMTP_PASS environment variables.', 503
        )

    scheduled = meeting['scheduled_at']
    date_str  = scheduled.strftime('%A, %d %B %Y at %H:%M') if scheduled else 'TBC'
    subject   = f"Meeting Invitation: {meeting['title']}"
    sent = failed = 0

    for member in members:
        body = f"""Dear {member['full_name'] or 'Member'},

You are invited to the following meeting:

Title:    {meeting['title']}
Date:     {date_str}
Location: {meeting['location'] or 'TBC'}

Agenda:
{meeting['agenda'] or 'No agenda provided'}

Please make every effort to attend.

IDMS System
"""
        try:
            msg = MIMEMultipart()
            msg['From']    = Config.SMTP_FROM or Config.SMTP_USER
            msg['To']      = member['email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)
            sent += 1
        except Exception:
            failed += 1

    log_action('meeting.invite', 'meeting', meeting_id, g.user['user_id'],
               {'sent': sent, 'failed': failed})
    return success({'sent': sent, 'failed': failed})


@meetings_bp.route('/<meeting_id>', methods=['PATCH'])
@require_auth
@require_admin
def update_meeting(meeting_id):
    data    = request.get_json() or {}
    allowed = {'title', 'scheduled_at', 'location', 'agenda'}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return error('No valid fields to update', 400)
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        set_clause = ', '.join(f"{k} = %s" for k in updates)
        cur.execute(
            f"UPDATE meetings SET {set_clause} WHERE id = %s",
            [*updates.values(), meeting_id]
        )
        conn.commit()
        return success({'message': 'Meeting updated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('/<meeting_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_meeting(meeting_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))
        conn.commit()
        return success({'message': 'Meeting deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
