import base64
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, g
from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor

from config import Config
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip()
    password  = data.get('password', '')

    if not full_name or not email or not password:
        return error('Full name, email, and password are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10))
        hashed_b64 = base64.b64encode(hashed).decode()

        cur.execute(
            """INSERT INTO users (full_name, email, password_hash, role)
               VALUES (%s, %s, %s, 'member') RETURNING id""",
            (full_name, email, hashed_b64)
        )
        user_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'user_id': user_id}, message='Account created successfully', status=201)

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
def get_profile():
    from middleware.auth import token_required
    from flask import g

    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        return error('Token missing', 401)
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
    except Exception as e:
        return error(f'Invalid token: {str(e)}', 401)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, full_name, email, role, is_active, created_at FROM users WHERE id = %s",
            (payload['user_id'],)
        )
        user = cur.fetchone()
        if not user:
            return error('User not found', 404)
        user['id'] = str(user['id'])
        return success({'user': dict(user)})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
