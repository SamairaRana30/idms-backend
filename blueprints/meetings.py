from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

meetings_bp = Blueprint('meetings', __name__, url_prefix='/api/v1/meetings')


@meetings_bp.route('', methods=['GET'])
@require_auth
def list_meetings():
    page, limit, offset = paginate(request)
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) FROM meetings")
        total = cur.fetchone()['count']

        cur.execute(
            """SELECT m.id, m.title, m.scheduled_at, m.location, m.agenda,
                      m.minutes, m.status, m.created_at, u.full_name AS created_by_name
               FROM meetings m JOIN users u ON u.id = m.created_by
               ORDER BY m.scheduled_at DESC LIMIT %s OFFSET %s""",
            (limit, offset)
        )
        meetings = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'meetings': meetings, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('', methods=['POST'])
@require_auth
@require_admin
def create_meeting():
    data = request.get_json() or {}
    title        = data.get('title', '').strip()
    scheduled_at = data.get('scheduled_at')
    location     = data.get('location', '')
    agenda       = data.get('agenda', '')

    if not title or not scheduled_at:
        return error('Title and scheduled_at are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO meetings (title, scheduled_at, location, agenda, created_by)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (title, scheduled_at, location, agenda, g.user['user_id'])
        )
        meeting_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'meeting_id': meeting_id}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@meetings_bp.route('/<meeting_id>', methods=['PATCH'])
@require_auth
@require_admin
def update_meeting(meeting_id):
    data = request.get_json() or {}
    allowed = {'title', 'scheduled_at', 'location', 'agenda', 'minutes', 'status'}
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return error('No valid fields to update', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        set_clause = ', '.join(f"{k} = %s" for k in updates)
        cur.execute(f"UPDATE meetings SET {set_clause} WHERE id = %s", [*updates.values(), meeting_id])
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
        cur = conn.cursor()
        cur.execute("DELETE FROM meetings WHERE id = %s", (meeting_id,))
        conn.commit()
        return success({'message': 'Meeting deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
