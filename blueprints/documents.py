import uuid
from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db, get_supabase
from utils.helpers import success, error, paginate

documents_bp = Blueprint('documents', __name__, url_prefix='/api/v1/documents')

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.jpg', '.jpeg', '.png', '.xlsx'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@documents_bp.route('/upload', methods=['POST'])
@require_auth
def upload_document():
    if 'file' not in request.files:
        return error('No file provided', 400)

    file      = request.files['file']
    title     = request.form.get('title', '').strip()
    category  = request.form.get('category', '').strip()
    is_public = request.form.get('is_public', 'false').lower() == 'true'

    if not title:
        return error('Title is required', 400)

    filename  = file.filename or ''
    mime_type = file.content_type or ''
    ext       = ('.' + filename.rsplit('.', 1)[-1].lower()) if '.' in filename else ''

    if ext not in ALLOWED_EXTENSIONS:
        return error(f'Extension {ext} not allowed. Accepted: pdf, docx, jpg, png, xlsx', 400)
    if mime_type not in ALLOWED_MIME_TYPES:
        return error(f'MIME type {mime_type} not allowed', 400)

    file_bytes = file.read()
    if len(file_bytes) > MAX_BYTES:
        return error('File size exceeds 10 MB limit', 400)

    storage_path = f"{str(uuid.uuid4())}{ext}"

    try:
        sb = get_supabase()
        sb.storage.from_('documents').upload(
            path=storage_path,
            file=file_bytes,
            file_options={'content-type': mime_type}
        )
    except Exception as e:
        return error(f'Storage upload failed: {str(e)}', 500)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO documents (title, file_path, file_type, category, uploaded_by, is_public) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (title, storage_path, ext.lstrip('.'), category, g.user['user_id'], is_public)
        )
        doc_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'document_id': doc_id, 'storage_path': storage_path}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        try:
            get_supabase().storage.from_('documents').remove([storage_path])
        except Exception:
            pass
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('', methods=['GET'])
@require_auth
def list_documents():
    page, limit, offset = paginate(request)
    category = request.args.get('category', '').strip()
    is_admin = g.user.get('role') == 'admin'

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        visibility = "" if is_admin else "AND d.is_public = true"
        cat_filter = "AND d.category ILIKE %s" if category else ""
        params_count = []
        params_list  = []

        if not is_admin:
            params_count.append('%')
            params_list.append('%')
        if category:
            params_count.append(f'%{category}%')
            params_list.append(f'%{category}%')

        count_sql = f"""
            SELECT COUNT(*) FROM documents d
            WHERE true {visibility} {cat_filter}
        """
        cur.execute(count_sql, params_count)
        total = cur.fetchone()['count']

        list_sql = f"""
            SELECT d.id, d.title, d.file_path, d.file_type, d.category,
                   d.is_public, d.created_at, u.full_name AS uploaded_by_name
            FROM documents d JOIN users u ON u.id = d.uploaded_by
            WHERE true {visibility} {cat_filter}
            ORDER BY d.created_at DESC LIMIT %s OFFSET %s
        """
        cur.execute(list_sql, [*params_list, limit, offset])
        docs = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'documents': docs, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('/search', methods=['GET'])
@require_auth
def search_documents():
    q        = request.args.get('q', '').strip()
    is_admin = g.user.get('role') == 'admin'

    if not q:
        return error('Search query required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        visibility = "" if is_admin else "AND d.is_public = true"
        term = f'%{q}%'
        cur.execute(
            f"""SELECT d.id, d.title, d.file_path, d.file_type, d.category,
                       d.is_public, d.created_at, u.full_name AS uploaded_by_name
                FROM documents d JOIN users u ON u.id = d.uploaded_by
                WHERE (d.title ILIKE %s OR d.category ILIKE %s) {visibility}
                ORDER BY d.created_at DESC LIMIT 50""",
            (term, term)
        )
        docs = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'documents': docs, 'total': len(docs), 'query': q})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('/<doc_id>/download', methods=['GET'])
@require_auth
def download_document(doc_id):
    is_admin = g.user.get('role') == 'admin'
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, file_path, is_public FROM documents WHERE id = %s",
            (doc_id,)
        )
        doc = cur.fetchone()
        if not doc:
            return error('Document not found', 404)
        if not is_admin and not doc['is_public']:
            return error('Access denied', 403)

        sb     = get_supabase()
        result = sb.storage.from_('documents').create_signed_url(doc['file_path'], 3600)
        # supabase-py v2 returns a dict with 'signedURL' key
        url = (result or {}).get('signedURL') or (result or {}).get('signedUrl', '')
        if not url and isinstance(result, dict):
            data = result.get('data') or {}
            url  = data.get('signedURL') or data.get('signedUrl', '')

        if not url:
            return error('Could not generate download link', 500)

        return success({'download_url': url})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@documents_bp.route('/<doc_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_document(doc_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT file_path FROM documents WHERE id = %s", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            return error('Document not found', 404)

        storage_path = doc['file_path']

        # Hard delete from DB
        cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        conn.commit()

        # Remove from Supabase Storage
        try:
            get_supabase().storage.from_('documents').remove([storage_path])
        except Exception:
            pass  # DB record is gone; storage orphan is acceptable

        return success({'message': 'Document deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
