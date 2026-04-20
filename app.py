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

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'my_super_secret_key_12345')

# Database connection function
def get_db_connection(environment='dev'):
    if environment == 'dev':
        url = os.getenv('DEV_DATABASE_URL')
    elif environment == 'staging':
        url = os.getenv('STAGING_DATABASE_URL')
    else:
        url = os.getenv('PROD_DATABASE_URL')
    
    if not url:
        raise Exception(f"Database URL not found for environment: {environment}")
    
    return psycopg2.connect(url)

# JWT decorator
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

# ============ ROOT ENDPOINTS ============
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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if test_database() else 'disconnected'
    })

def test_database():
    """Test database connection"""
    try:
        conn = get_db_connection('dev')
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except:
        return False

# ============ AUTHENTICATION ============
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    env = data.get('environment', 'dev')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Check password
        stored_hash = user['password_hash'].encode('utf-8')
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
        
        return jsonify({'error': 'Invalid password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    env = data.get('environment', 'dev')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (email, hashed.decode('utf-8'), 'user')
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'User created', 'user_id': user_id}), 201
    except psycopg2.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ USERS ============
@app.route('/api/v1/users', methods=['GET'])
@token_required
def get_users():
    env = request.args.get('environment', 'dev')
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, email, role, is_active, created_at FROM users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ INITIALIZE TEST DATA ============
@app.route('/api/v1/init', methods=['POST'])
def init_test_data():
    """Create test admin user (password: Test@123)"""
    env = request.args.get('environment', 'dev')
    
    hashed = bcrypt.hashpw('Test@123'.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor()
        
        # Check if admin exists
        cur.execute("SELECT id FROM users WHERE email = %s", ('admin@test.com',))
        existing = cur.fetchone()
        
        if not existing:
            cur.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
                ('admin@test.com', hashed.decode('utf-8'), 'admin')
            )
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Test admin created'})
        else:
            cur.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Test admin already exists'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ NOTIFICATIONS ============
@app.route('/api/v1/notifications', methods=['GET'])
@token_required
def get_notifications():
    env = request.args.get('environment', 'dev')
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM notifications ORDER BY created_at DESC")
        notifications = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/notifications', methods=['POST'])
@token_required
def create_notification():
    data = request.get_json()
    env = data.get('environment', 'dev')
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notifications (type, recipient, message, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (data.get('type'), data.get('recipient'), data.get('message'), 'pending')
        )
        notification_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Notification created', 'id': notification_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port)