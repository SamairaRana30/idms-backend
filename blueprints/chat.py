from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error
from utils.audit import log_action

chat_bp = Blueprint('chat', __name__, url_prefix='/api/v1/chat')

_SCHEMA_INIT = False


def ensure_tables():
    global _SCHEMA_INIT
    if _SCHEMA_INIT:
        return
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_channels (
                id          SERIAL PRIMARY KEY,
                name        VARCHAR(80) NOT NULL UNIQUE,
                description TEXT,
                created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id          SERIAL PRIMARY KEY,
                channel_id  INTEGER NOT NULL REFERENCES chat_channels(id) ON DELETE CASCADE,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content     TEXT    NOT NULL,
                reply_to_id INTEGER REFERENCES chat_messages(id) ON DELETE SET NULL,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM chat_channels")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO chat_channels (name, description) VALUES (%s, %s)",
                ('general', 'General discussion')
            )
            conn.commit()
        _SCHEMA_INIT = True
    except Exception as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f'Chat table setup failed: {e}') from e
    finally:
        close_db(conn, cur)


# ── Channels ───────────────────────────────────────────────────────────────────

def _ensure_or_error():
    try:
        ensure_tables()
        return None
    except RuntimeError as e:
        return error(str(e), 500)


@chat_bp.route('/channels', methods=['GET'])
@require_auth
def list_channels():
    err = _ensure_or_error()
    if err: return err
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT c.id, c.name, c.description, c.created_at,
                   (SELECT m.content FROM chat_messages m
                    WHERE m.channel_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_message
            FROM chat_channels c
            ORDER BY c.name ASC
        """)
        channels = [dict(r) for r in cur.fetchall()]
        return success({'channels': channels})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@chat_bp.route('/channels', methods=['POST'])
@require_auth
@require_admin
def create_channel():
    err = _ensure_or_error()
    if err: return err
    data = request.get_json() or {}
    name = (data.get('name') or '').strip().lower().replace(' ', '-')
    description = (data.get('description') or '').strip()
    if not name:
        return error('Channel name is required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO chat_channels (name, description, created_by) VALUES (%s, %s, %s) RETURNING *",
            (name, description or None, g.user['user_id'])
        )
        channel = dict(cur.fetchone())
        conn.commit()
        log_action(g.user['user_id'], 'create_channel', 'chat_channel', str(channel['id']), {'name': name})
        return success({'channel': channel}, 201)
    except Exception as e:
        if conn: conn.rollback()
        if 'unique' in str(e).lower():
            return error(f'A channel named #{name} already exists', 409)
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@chat_bp.route('/channels/<int:channel_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_channel(channel_id):
    err = _ensure_or_error()
    if err: return err
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT name FROM chat_channels WHERE id = %s", (channel_id,))
        row = cur.fetchone()
        if not row:
            return error('Channel not found', 404)
        cur.execute("DELETE FROM chat_messages WHERE channel_id = %s", (channel_id,))
        cur.execute("DELETE FROM chat_channels WHERE id = %s", (channel_id,))
        conn.commit()
        return success({'message': 'Channel deleted'})
    except Exception as e:
        if conn: conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


# ── Messages ───────────────────────────────────────────────────────────────────

@chat_bp.route('/channels/<int:channel_id>/messages', methods=['GET'])
@require_auth
def list_messages(channel_id):
    err = _ensure_or_error()
    if err: return err
    after_id = request.args.get('after', 0, type=int)
    limit    = min(request.args.get('limit', 50, type=int), 200)
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT m.id, m.channel_id, m.user_id, m.content, m.reply_to_id, m.created_at,
                   u.full_name, u.email,
                   r.content   AS reply_to_content,
                   ru.full_name AS reply_to_author
            FROM chat_messages m
            JOIN users u  ON u.id  = m.user_id
            LEFT JOIN chat_messages r  ON r.id  = m.reply_to_id
            LEFT JOIN users         ru ON ru.id = r.user_id
            WHERE m.channel_id = %s AND m.id > %s
            ORDER BY m.created_at ASC
            LIMIT %s
        """, (channel_id, after_id, limit))
        messages = [dict(r) for r in cur.fetchall()]
        return success({'messages': messages})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@chat_bp.route('/channels/<int:channel_id>/messages', methods=['POST'])
@require_auth
def post_message(channel_id):
    err = _ensure_or_error()
    if err: return err
    data     = request.get_json() or {}
    content  = (data.get('content') or '').strip()
    reply_to = data.get('reply_to_id')
    if not content:
        return error('Message content is required', 400)
    if len(content) > 4000:
        return error('Message too long (max 4000 chars)', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id FROM chat_channels WHERE id = %s", (channel_id,))
        if not cur.fetchone():
            return error('Channel not found', 404)

        cur.execute("""
            INSERT INTO chat_messages (channel_id, user_id, content, reply_to_id)
            VALUES (%s, %s, %s, %s) RETURNING id, created_at
        """, (channel_id, g.user['user_id'], content, reply_to or None))
        row = cur.fetchone()
        conn.commit()
        return success({'message': {'id': row['id'], 'created_at': str(row['created_at'])}}, 201)
    except Exception as e:
        if conn: conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
