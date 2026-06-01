from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import token_required, admin_required
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


@users_bp.route('', methods=['GET'])
@token_required
@admin_required
def get_users():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, full_name, email, role, is_active, created_at FROM users ORDER BY created_at DESC"
        )
        users = [dict(u) | {'id': str(u['id'])} for u in cur.fetchall()]
        return success({'users': users})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/<user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, full_name, email, role, is_active, created_at FROM users WHERE id = %s",
            (user_id,)
        )
        user = cur.fetchone()
        if not user:
            return error('User not found', 404)
        return success({'user': dict(user) | {'id': str(user['id'])}})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/<user_id>', methods=['PATCH'])
@token_required
@admin_required
def update_user(user_id):
    data = request.get_json() or {}
    allowed = {'full_name', 'role', 'is_active'}
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return error('No valid fields to update', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        set_clause = ', '.join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [user_id]
        cur.execute(f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = %s", values)
        conn.commit()
        return success(message='User updated')
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/<user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    if g.user['user_id'] == user_id:
        return error('Cannot delete your own account', 400)
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return success(message='User deleted')
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
