import base64
import bcrypt
from flask import Blueprint
from config import Config
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

migration_bp = Blueprint('migration', __name__, url_prefix='/api/v1')


@migration_bp.route('/init', methods=['POST'])
def init_test_data():
    """Seed a test admin user — development only."""
    if Config.ENV != 'development':
        return error('Not allowed outside development', 403)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", ('admin@idms.com',))
        if cur.fetchone():
            return success(message='Admin user already exists')

        hashed = bcrypt.hashpw(b'Admin@1234', bcrypt.gensalt(10))
        hashed_b64 = base64.b64encode(hashed).decode()
        cur.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, 'admin')",
            ('IDMS Admin', 'admin@idms.com', hashed_b64)
        )
        conn.commit()
        return success(message='Admin user created. Email: admin@idms.com / Password: Admin@1234', status=201)

    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@migration_bp.route('/health', methods=['GET'])
def health_check():
    from datetime import datetime
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        db_status = 'connected'
    except Exception as e:
        db_status = f'disconnected: {str(e)}'

    return success({
        'database': db_status,
        'environment': Config.ENV,
        'schema': Config.get_schema(),
        'timestamp': datetime.utcnow().isoformat()
    })
