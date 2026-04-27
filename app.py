import os
import base64
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

jwt_secret = os.getenv('JWT_SECRET')
if not jwt_secret:
    raise Exception("JWT_SECRET environment variable not set")
app.config['JWT_SECRET'] = jwt_secret


def get_db_connection():
    """Get a database connection using the Session Pooler URL."""
    database_url = os.getenv('DEV_DATABASE_URL')
    if not database_url:
        raise Exception("DEV_DATABASE_URL environment variable not set")

    conn = psycopg2.connect(database_url)

    with conn.cursor() as cur:
        cur.execute("SET search_path TO idms_dev")
    conn.commit()

    return conn


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'error': 'Token missing'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            g.user = data
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid token: {str(e)}'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'IDMS API is running!',
        'status': 'online',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/v1/health',
            'login': '/api/v1/auth/login (POST)',
            'register': '/api/v1/auth/register (POST)',
            'users': '/api/v1/users (GET)',
            'init': '/api/v1/init (POST)'
        }
    })


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/init', methods=['POST'])
def init_test_data():
    """Create test admin user (password: Test@123) - dev only."""
    if os.getenv("ENV", "development") != "development":
        return jsonify({'success': False, 'error': 'Not allowed outside development'}), 403

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        password = 'Test@123'
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        hashed_b64 = base64.b64encode(hashed_password).decode('utf-8')

        cur.execute("SELECT id FROM users WHERE email = %s", ('admin@test.com',))
        existing_user = cur.fetchone()

        if not existing_user:
            cur.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
                ('admin@test.com', hashed_b64, 'admin')
            )
            conn.commit()
            message = 'Test admin user created successfully.'
        else:
            message = 'Test admin user already exists.'

        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': message})

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401

        stored_hash = base64.b64decode(user['password_hash'].encode('utf-8'))

        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET'], algorithm='HS256')

            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'role': user['role']
                }
            })

        return jsonify({'success': False, 'error': 'Invalid password'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_b64 = base64.b64encode(hashed).decode('utf-8')

        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (email, hashed_b64, 'user')
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'User created', 'user_id': user_id}), 201
    except IntegrityError:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': 'Email already exists'}), 409
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/users', methods=['GET'])
@token_required
def get_users():
    """Get all users (protected endpoint)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, email, role, is_active, created_at FROM users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port)

    