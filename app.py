import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'my_super_secret_key_12345')

def get_db_connection():
    """Get a database connection and set the correct schema"""
    database_url = os.getenv('DEV_DATABASE_URL')
    if not database_url:
        raise Exception("DEV_DATABASE_URL environment variable not set")

    # Connect using the clean URL
    conn = psycopg2.connect(database_url)

    # Set the search path to your 'idms_dev' schema for all queries in this connection
    with conn.cursor() as cur:
        cur.execute("SET search_path TO idms_dev")

    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            request.user = data
        except Exception as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401
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
    """Create test admin user (password: Test@123) in the idms_dev schema"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        hashed_password = bcrypt.hashpw('Test@123'.encode('utf-8'), bcrypt.gensalt())

        # Check if admin already exists
        cur.execute("SELECT id FROM users WHERE email = %s", ('admin@test.com',))
        existing_user = cur.fetchone()

        if not existing_user:
            cur.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
                ('admin@test.com', hashed_password.decode('utf-8'), 'admin')
            )
            conn.commit()
            message = 'Test admin user created successfully.'
        else:
            message = 'Test admin user already exists.'

        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': message})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return jsonify({'error': 'User not found'}), 401

        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
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

        return jsonify({'error': 'Invalid password'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port)