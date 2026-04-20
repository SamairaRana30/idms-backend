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

app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'mysecretkey')

def get_db_connection(environment='dev'):
    if environment == 'dev':
        url = os.getenv('DEV_DATABASE_URL')
    elif environment == 'staging':
        url = os.getenv('STAGING_DATABASE_URL')
    else:
        url = os.getenv('PROD_DATABASE_URL')
    
    return psycopg2.connect(url)

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
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    env = data.get('environment', 'dev')
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET'], algorithm='HS256')
            
            return jsonify({'token': token, 'user': {'id': user['id'], 'email': user['email'], 'role': user['role']}})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    env = data.get('environment', 'dev')
    
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
        
        return jsonify({'message': 'User created', 'user_id': user_id}), 201
    except psycopg2.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/init', methods=['POST'])
def init_test_data():
    env = request.args.get('environment', 'dev')
    
    hashed = bcrypt.hashpw('Test@123'.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db_connection(env)
        cur = conn.cursor()
        
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
            return jsonify({'message': 'Test admin created'})
        else:
            cur.close()
            conn.close()
            return jsonify({'message': 'Test admin already exists'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)