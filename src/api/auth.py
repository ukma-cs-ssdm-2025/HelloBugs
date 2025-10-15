from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timezone, timedelta
import os
from secrets import compare_digest
from .models.user_model import User
from .db import db

# Security: Validate SECRET_KEY
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("Змінна середовища SECRET_KEY обов'язкова для JWT!")

JWT_CONFIG = {
    'algorithm': 'HS256',
    'audience': 'hotel-reservation-api',
    'issuer': 'hotel-auth-service'
}


def create_token(user_id, role=None, is_admin=False):
    """Generate secure JWT token for a user"""
    payload = {
        'user_id': user_id,
        'role': role,
        'is_admin': is_admin,
        'exp': datetime.now(timezone.utc) + timedelta(days=1),
        'aud': JWT_CONFIG['audience'],
        'iss': JWT_CONFIG['issuer'],
        'iat': datetime.now(timezone.utc)  # Issued at
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_CONFIG['algorithm'])


def token_required(f):
    """Secure decorator to require authentication"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Secure header parsing (timing attack resistant)
        auth_header = request.headers.get('Authorization', '')
        if auth_header and compare_digest(auth_header[:7], 'Bearer '):
            token = auth_header[7:]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Secure token decoding with algorithm verification
            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[JWT_CONFIG['algorithm']],
                audience=JWT_CONFIG['audience'],
                issuer=JWT_CONFIG['issuer']
            )

            # Get user from database
            current_user = db.query(User).get(data['user_id'])

            if not current_user:
                return jsonify({'message': 'User not found'}), 401

            # Add user to Flask's g object
            g.current_user = current_user
            g.is_admin = data.get('is_admin', False)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            # Don't expose specific error details
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Secure decorator to require admin privileges"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'is_admin') or not g.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)

    return decorated


def staff_required(f):
    """Secure decorator to require staff privileges"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({'message': 'Authentication required'}), 401

        # Secure role checking
        if not hasattr(g.current_user, 'role'):
            return jsonify({'message': 'Invalid user role'}), 403

        user_role = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role

        if user_role not in ['STAFF', 'ADMIN']:
            return jsonify({'message': 'Staff access required'}), 403
        return f(*args, **kwargs)

    return decorated


def role_required(*allowed_roles):
    """Secure decorator to require specific roles"""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'message': 'Authentication required'}), 401

            if not hasattr(g.current_user, 'role'):
                return jsonify({'message': 'Invalid user role'}), 403

            user_role = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role

            if user_role not in allowed_roles:
                return jsonify({'message': 'Access denied'}), 403  # Don't expose required roles
            return f(*args, **kwargs)

        return decorated

    return decorator


def login_required_web(f):
    """Secure decorator for web routes"""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth_token')

        # Secure header parsing
        if not token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header and compare_digest(auth_header[:7], 'Bearer '):
                token = auth_header[7:]

        if not token:
            return jsonify({'message': 'Authentication required'}), 401

        try:
            # Secure token validation
            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[JWT_CONFIG['algorithm']],
                audience=JWT_CONFIG['audience'],
                issuer=JWT_CONFIG['issuer']
            )

            current_user = db.query(User).get(data['user_id'])

            if not current_user:
                return jsonify({'message': 'User not found'}), 401

            g.current_user = current_user
            g.is_admin = data.get('is_admin', False)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated
