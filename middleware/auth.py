import os
from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Token missing', 'code': 401}), 401
        try:
            token = auth_header.split(' ')[1]
            data = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            g.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired', 'code': 401}), 401
        except Exception as e:
            return jsonify({'success': False, 'error': 'Invalid token', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required', 'code': 403}), 403
        return f(*args, **kwargs)
    return decorated
