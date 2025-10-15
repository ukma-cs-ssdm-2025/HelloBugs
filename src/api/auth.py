from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timedelta
import os
from .models.user_model import User
from .db import db

SECRET_KEY = os.getenv('SECRET_KEY')

def create_token(user_id, role=None, is_admin=False):
    """Generate JWT token for a user"""
    payload = {
        'user_id': user_id,
        'role': role,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            # Get the user from the database
            current_user = db.query(User).get(data['user_id'])

            if not current_user:
                return jsonify({'message': 'User not found'}), 401

            # Add user to Flask's g object
            g.current_user = current_user
            g.is_admin = data.get('is_admin', False)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'is_admin') or not g.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    """Decorator to require staff privileges (STAFF or ADMIN)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({'message': 'Authentication required'}), 401

        user_role = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role

        if user_role not in ['STAFF', 'ADMIN']:
            return jsonify({'message': 'Staff access required'}), 403
        return f(*args, **kwargs)
    return decorated

def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'message': 'Authentication required'}), 401

            user_role = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role

            if user_role not in allowed_roles:
                return jsonify({'message': f'Access denied'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def login_required_web(f):
    """Decorator for web routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for token in cookies or session
        token = request.cookies.get('auth_token')
        if not token:
            # Check Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Authentication required'}), 401

        try:
            # Decode the token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            # Get the user from the database
            current_user = db.query(User).get(data['user_id'])

            if not current_user:
                return jsonify({'message': 'User not found'}), 401

            # Add user to Flask's g object
            g.current_user = current_user
            g.is_admin = data.get('is_admin', False)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated
