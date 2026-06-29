import io
import base64
import bcrypt
from datetime import datetime

import pandas as pd
from flask import Blueprint, request
from psycopg2.extras import RealDictCursor

from config import Config
from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

migration_bp = Blueprint('migration', __name__, url_prefix='/api/v1')


@migration_bp.route('/init', methods=['POST'])
def init_test_data():
    if Config.ENV != 'development':
        return error('Not allowed outside development', 403)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", ('admin@test.com',))
        if cur.fetchone():
            return success({'message': 'Admin user already exists'})

        hashed = bcrypt.hashpw(b'Test@123', bcrypt.gensalt(12))
        hashed_b64 = base64.b64encode(hashed).decode()
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, 'admin')",
            ('Test Admin', 'admin@test.com', hashed_b64)
        )
        conn.commit()
        return success({'message': 'Admin created. Email: admin@test.com / Password: Test@123'}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@migration_bp.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'

    return success({
        'status':      'ok',
        'version':     '2.0',
        'database':    db_status,
        'environment': Config.ENV,
        'schema':      Config.get_schema()
    })


def _parse_file(file):
    filename = file.filename.lower()
    raw = file.read()
    if filename.endswith('.csv'):
        return pd.read_csv(io.BytesIO(raw))
    elif filename.endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(raw))
    return None


@migration_bp.route('/migration/upload', methods=['POST'])
@require_auth
@require_admin
def migration_upload():
    if 'file' not in request.files:
        return error('No file provided', 400)

    file = request.files['file']
    try:
        df = _parse_file(file)
    except Exception as e:
        return error(f'Failed to parse file: {str(e)}', 400)

    if df is None:
        return error('Only CSV and Excel (.xlsx, .xls) files are accepted', 400)

    total_rows = len(df)
    columns    = list(df.columns)

    missing_email = int(df['email'].isna().sum()) if 'email' in df.columns else total_rows

    if 'email' in df.columns:
        emails = df['email'].dropna().astype(str).str.lower().str.strip()
        duplicate_emails = int((emails.value_counts() > 1).sum())
    else:
        duplicate_emails = 0

    preview = df.head(10).fillna('').astype(str).to_dict(orient='records')

    return success({
        'preview':  preview,
        'columns':  columns,
        'stats': {
            'total_rows':      total_rows,
            'duplicate_emails': duplicate_emails,
            'missing_email':   missing_email
        }
    })


@migration_bp.route('/migration/import', methods=['POST'])
@require_auth
@require_admin
def migration_import():
    if 'file' not in request.files:
        return error('No file provided', 400)

    file = request.files['file']
    try:
        df = _parse_file(file)
    except Exception as e:
        return error(f'Failed to parse file: {str(e)}', 400)

    if df is None:
        return error('Only CSV and Excel (.xlsx, .xls) files are accepted', 400)

    if 'email' not in df.columns:
        return error('File must contain an email column', 400)

    # --- Clean ---
    df['email'] = df['email'].astype(str).str.lower().str.strip()

    if 'full_name' in df.columns:
        df['full_name'] = df['full_name'].astype(str).str.strip().str.title()
    elif 'name' in df.columns:
        df['full_name'] = df['name'].astype(str).str.strip().str.title()
    else:
        df['full_name'] = 'Imported User'

    if 'phone' in df.columns:
        df['phone'] = df['phone'].astype(str).str.replace(r'\D', '', regex=True)

    # --- Drop missing email ---
    missing_mask     = df['email'].isin(['', 'nan', 'none'])
    skipped_missing  = int(missing_mask.sum())
    df = df[~missing_mask].copy()

    # --- Drop duplicates within file (keep first) ---
    before_dedup       = len(df)
    df = df.drop_duplicates(subset='email', keep='first')
    skipped_file_dups  = before_dedup - len(df)

    # --- Drop emails already in DB ---
    conn = cur = None
    inserted           = 0
    skipped_db_dups    = 0
    errors             = []

    try:
        conn = get_db()
        cur  = conn.cursor()

        emails = df['email'].tolist()
        if emails:
            cur.execute("SELECT email FROM users WHERE email = ANY(%s)", (emails,))
            existing = {row[0] for row in cur.fetchall()}
        else:
            existing = set()

        df = df[~df['email'].isin(existing)]
        skipped_db_dups = len(emails) - len(df)

        if not df.empty:
            # One temp hash for all imported rows (same default password)
            temp_hash = bcrypt.hashpw(b'ChangeMe@123', bcrypt.gensalt(12))
            temp_b64  = base64.b64encode(temp_hash).decode()

            chunk_size = 500
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i + chunk_size]
                rows  = [
                    (row.get('full_name', 'Imported User'), row['email'], temp_b64)
                    for _, row in chunk.iterrows()
                ]
                try:
                    cur.executemany(
                        "INSERT INTO users (full_name, email, password_hash, role, is_active) "
                        "VALUES (%s, %s, %s, 'member', true)",
                        rows
                    )
                    inserted += len(rows)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    errors.append(f'Chunk {i // chunk_size + 1}: {str(e)}')

        return success({
            'inserted':              inserted,
            'skipped_duplicates':    skipped_file_dups + skipped_db_dups,
            'skipped_missing_email': skipped_missing,
            'errors':                errors[:10]
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
