from flask import Blueprint, request
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

audit_bp = Blueprint('audit', __name__, url_prefix='/api/v1/audit')


@audit_bp.route('', methods=['GET'])
@require_auth
@require_admin
def get_audit_logs():
    page, limit, offset = paginate(request)
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) FROM audit_logs")
        total = cur.fetchone()['count']

        cur.execute(
            """SELECT al.id, al.action, al.entity, al.entity_id,
                      al.details, al.created_at,
                      u.full_name AS performed_by_name,
                      u.email     AS performed_by_email
               FROM audit_logs al
               LEFT JOIN users u ON u.id = al.performed_by
               ORDER BY al.created_at DESC
               LIMIT %s OFFSET %s""",
            (limit, offset)
        )
        logs = [
            dict(r) | {'id': str(r['id']), 'entity_id': str(r['entity_id']) if r['entity_id'] else None}
            for r in cur.fetchall()
        ]
        return success({'logs': logs, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
