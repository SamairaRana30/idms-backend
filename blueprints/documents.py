from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

documents_bp = Blueprint('documents', __name__, url_prefix='/api/v1/documents')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {
    'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain', 'text/csv',
    'image/png', 'image/jpeg'
}


def validate_file(filename, mime_type):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return f"File extension '.{ext}' not allowed"
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        return f"MIME type '{mime_type}' not allowed"
    return None


@documents_bp.route('', methods=['GET'])
@require_auth
def list_documents():
    page, limit, offset = paginate(request)
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """SELECT COUNT(*) FROM documents d
               WHERE d.is_public = true OR d.uploaded_by = %s""",
            (g.user['user_id'],)
        )
        total = cur.fetchone()['count']

        cur.execute(
            """SELECT d.id, d.title, d.file_path, d.file_type, d.category,
                      d.is_public, d.created_at, u.full_name AS uploaded_by_name
               FROM documents d JOIN users u ON u.id = d.uploaded_by
               WHERE d.is_public = true OR d.uploaded_by = %s
               ORDER BY d.created_at DESC LIMIT %s OFFSET %s""",
            (g.user['user_id'], limit, offset)
        )
        docs = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'documents': docs, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('', methods=['POST'])
@require_auth
def create_document():
    data = request.get_json() or {}
    title     = data.get('title', '').strip()
    file_path = data.get('file_path', '').strip()
    file_type = data.get('file_type', '').strip()
    mime_type = data.get('mime_type', '')
    category  = data.get('category', '').strip()
    is_public = bool(data.get('is_public', False))

    if not title or not file_path:
        return error('Title and file_path are required', 400)

    filename = file_path.split('/')[-1]
    validation_error = validate_file(filename, mime_type)
    if validation_error:
        return error(validation_error, 400)

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
        return success({'document_id': doc_id}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('/<doc_id>', methods=['DELETE'])
@require_auth
def delete_document(doc_id):
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT uploaded_by FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return error('Document not found', 404)

        is_owner = str(doc['uploaded_by']) == g.user['user_id']
        is_admin = g.user['role'] == 'admin'
        if not is_owner and not is_admin:
            return error('Not authorised to delete this document', 403)

        # Soft delete — set is_public=false to hide, keep record
        cur.execute("UPDATE documents SET is_public = false WHERE id = %s", (doc_id,))
        conn.commit()
        return success({'message': 'Document removed'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
