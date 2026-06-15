import os
from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config

# In-memory revocation list keyed by JTI. Persists for the lifetime of the
# process (single Gunicorn worker on Render). Sufficient for this project.
_revoked_jtis: set = set()


def revoke_jti(jti: str) -> None:
    _revoked_jtis.add(jti)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Token missing', 'code': 401}), 401
        try:
            token = auth_header.split(' ')[1]
            data = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            jti = data.get('jti')
            if jti and jti in _revoked_jtis:
                return jsonify({'success': False, 'error': 'Token has been revoked', 'code': 401}), 401
            g.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired', 'code': 401}), 401
        except Exception:
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
