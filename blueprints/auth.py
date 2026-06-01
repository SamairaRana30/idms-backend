import re
import base64
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, g
from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor

from config import Config
from middleware.auth import require_auth
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip().lower()
    password  = data.get('password', '')

    if not full_name or not email or not password:
        return error('Full name, email, and password are required', 400)
    if not _EMAIL_RE.match(email):
        return error('Invalid email format', 400)
    if len(password) < 8:
        return error('Password must be at least 8 characters', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12))
        hashed_b64 = base64.b64encode(hashed).decode()

        cur.execute(
            """INSERT INTO users (full_name, email, password_hash, role)
               VALUES (%s, %s, %s, 'member') RETURNING id, email, role""",
            (full_name, email, hashed_b64)
        )
        row = cur.fetchone()
        conn.commit()
        return success({'user_id': str(row[0]), 'email': row[1], 'role': row[2]}, 201)

    except IntegrityError:
        if conn:
            conn.rollback()
        return error('Email already registered', 409)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email    = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return error('Email and password required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s AND is_active = true", (email,))
        user = cur.fetchone()

        if not user:
            return error('Invalid email or password', 401)

        stored = base64.b64decode(user['password_hash'].encode())
        if not bcrypt.checkpw(password.encode(), stored):
            return error('Invalid email or password', 401)

        token = jwt.encode({
            'user_id':   str(user['id']),
            'email':     user['email'],
            'full_name': user['full_name'],
            'role':      user['role'],
            'exp':       datetime.now(timezone.utc) + timedelta(hours=24)
        }, Config.JWT_SECRET, algorithm='HS256')

        return success({
            'token': token,
            'user': {
                'id':        str(user['id']),
                'full_name': user['full_name'],
                'email':     user['email'],
                'role':      user['role']
            }
        })

    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
