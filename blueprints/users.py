import re
import uuid
from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db, get_supabase
from utils.helpers import success, error, paginate
from utils.audit import log_action

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@users_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(
                "SELECT id, full_name, email, role, is_active, created_at, photo_url FROM users WHERE id = %s",
                (g.user['user_id'],)
            )
        except Exception:
            conn.rollback()
            cur.execute(
                "SELECT id, full_name, email, role, is_active, created_at FROM users WHERE id = %s",
                (g.user['user_id'],)
            )
        user = cur.fetchone()
        if not user:
            return error('User not found', 404)
        return success({'user': dict(user) | {'id': str(user['id'])}})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/me', methods=['PUT'])
@require_auth
def update_me():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip().lower()

    updates = {}
    if full_name:
        updates['full_name'] = full_name
    if email:
        if not _EMAIL_RE.match(email):
            return error('Invalid email format', 400)
        updates['email'] = email

    if not updates:
        return error('Nothing to update', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        set_clause = ', '.join(f"{k} = %s" for k in updates)
        cur.execute(
            f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = %s",
            [*updates.values(), g.user['user_id']]
        )
        conn.commit()
        log_action('user.update_self', 'user', g.user['user_id'], g.user['user_id'], updates)
        return success({'message': 'Profile updated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('', methods=['GET'])
@require_auth
@require_admin
def get_users():
    page, limit, offset = paginate(request)
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()['count']

        cur.execute(
            "SELECT id, full_name, email, role, is_active, created_at "
            "FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        users = [dict(u) | {'id': str(u['id'])} for u in cur.fetchall()]
        return success({'users': users, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/me/photo', methods=['POST'])
@require_auth
def upload_photo():
    if 'photo' not in request.files:
        return error('No photo provided', 400)
    file      = request.files['photo']
    mime_type = file.content_type or ''
    if mime_type not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif'):
        return error('Only JPEG, PNG, WebP or GIF images are allowed', 400)

    ext        = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif'}.get(mime_type, '.jpg')
    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        return error('Image must be under 5 MB', 400)

    user_id      = g.user['user_id']
    storage_path = f"avatars/{user_id}{ext}"
    try:
        sb = get_supabase()
        try:
            sb.storage.from_('avatars').remove([storage_path])
        except Exception:
            pass
        sb.storage.from_('avatars').upload(
            path=storage_path,
            file=file_bytes,
            file_options={'content-type': mime_type, 'upsert': 'true'}
        )
        public_url = sb.storage.from_('avatars').get_public_url(storage_path)
    except Exception as e:
        return error(f'Storage upload failed: {str(e)}', 500)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE users SET photo_url = %s, updated_at = NOW() WHERE id = %s",
            (public_url, user_id)
        )
        conn.commit()
    except Exception:
        if conn: conn.rollback()
    finally:
        close_db(conn, cur)

    return success({'photo_url': public_url})


@users_bp.route('/stats', methods=['GET'])
@require_auth
@require_admin
def get_stats():
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                COUNT(*)                                     AS total,
                COUNT(*) FILTER (WHERE is_active)            AS active,
                COUNT(*) FILTER (WHERE NOT is_active)        AS inactive,
                COUNT(*) FILTER (WHERE role = 'admin')       AS admins,
                COUNT(*) FILTER (WHERE role = 'member')      AS members
            FROM users
        """)
        counts = dict(cur.fetchone())

        cur.execute("""
            SELECT TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') AS month,
                   COUNT(*) AS new_members
            FROM users
            WHERE created_at >= NOW() - INTERVAL '6 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY DATE_TRUNC('month', created_at) ASC
        """)
        growth = [dict(r) for r in cur.fetchall()]

        return success({**{k: int(v) for k, v in counts.items()}, 'growth': growth})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/<user_id>', methods=['PUT'])
@require_auth
@require_admin
def update_user(user_id):
    data = request.get_json() or {}
    allowed = {'full_name', 'role', 'is_active'}
    updates = {k: v for k, v in data.items() if k in allowed}

    if user_id == g.user['user_id'] and updates.get('role') not in (None, 'admin'):
        return error('Cannot demote your own admin account', 400)

    if not updates:
        return error('No valid fields to update', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        set_clause = ', '.join(f"{k} = %s" for k in updates)
        cur.execute(
            f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = %s",
            [*updates.values(), user_id]
        )
        conn.commit()
        log_action('user.update', 'user', user_id, g.user['user_id'], updates)
        return success({'message': 'User updated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@users_bp.route('/<user_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_user(user_id):
    if g.user['user_id'] == user_id:
        return error('Cannot deactivate your own account', 400)
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET is_active = false, updated_at = NOW() WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        log_action('user.delete', 'user', user_id, g.user['user_id'])
        return success({'message': 'User deactivated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
