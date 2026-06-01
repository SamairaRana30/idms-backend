from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import token_required, admin_required
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

documents_bp = Blueprint('documents', __name__, url_prefix='/api/v1/documents')


@documents_bp.route('', methods=['GET'])
@token_required
def list_documents():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT d.id, d.title, d.file_type, d.category, d.is_public, d.created_at,
                      u.full_name AS uploaded_by_name
               FROM documents d
               JOIN users u ON u.id = d.uploaded_by
               WHERE d.is_public = true OR d.uploaded_by = %s
               ORDER BY d.created_at DESC""",
            (g.user['user_id'],)
        )
        docs = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'documents': docs})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('', methods=['POST'])
@token_required
def create_document():
    data = request.get_json() or {}
    title     = data.get('title', '').strip()
    file_path = data.get('file_path', '').strip()
    file_type = data.get('file_type', '').strip()
    category  = data.get('category', '').strip()
    is_public = bool(data.get('is_public', False))

    if not title or not file_path:
        return error('Title and file_path are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO documents (title, file_path, file_type, category, uploaded_by, is_public)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (title, file_path, file_type, category, g.user['user_id'], is_public)
        )
        doc_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'document_id': doc_id}, message='Document saved', status=201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('/<doc_id>', methods=['DELETE'])
@token_required
def delete_document(doc_id):
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM documents WHERE id = %s AND (uploaded_by = %s OR %s = 'admin')",
            (doc_id, g.user['user_id'], g.user['role'])
        )
        conn.commit()
        return success(message='Document deleted')
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
