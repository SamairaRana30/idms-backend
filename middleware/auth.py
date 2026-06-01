from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Token missing'}), 401
        try:
            token = auth_header.split(' ')[1]
            data = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            g.user = data
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid token: {str(e)}'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
