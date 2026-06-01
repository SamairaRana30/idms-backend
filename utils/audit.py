import json
from utils.supabase_client import get_db, close_db


def log_action(action, entity, entity_id=None, performed_by=None, details=None):
    """Record an admin action in audit_logs. Never raises — audit errors are always swallowed."""
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (action, entity, entity_id, performed_by, details) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                action,
                entity,
                str(entity_id)   if entity_id    else None,
                str(performed_by) if performed_by else None,
                json.dumps(details) if details    else None,
            )
        )
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
    finally:
        close_db(conn, cur)
