from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from .models.user_model import User
from .db import db

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key'

def create_token(user_id, role=None, is_admin=False):
    """Generate JWT token for a user"""
    payload = {
        'user_id': user_id,
        'role': role,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # PyJWT v1 returns bytes, v2 returns str
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

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


def token_optional(f):
    """Decorator for optional authentication (allows both authenticated and guest users)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if token:
            try:
                # Decode the token
                data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

                # Get the user from the database
                current_user = db.query(User).get(data['user_id'])

                if current_user:
                    # Add user to Flask's g object
                    g.current_user = current_user
                    g.is_admin = data.get('is_admin', False)

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                # Ignore token errors for optional auth
                pass

        return f(*args, **kwargs)

    return decorated


def is_token_expired(token: str) -> bool:
    """Check if a JWT token is expired without raising exceptions
    
    Returns True if token is expired or invalid, False if valid
    """
    try:
        jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return False
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return True


def _has_uppercase(password):
    return any(char.isupper() for char in password)

def _has_lowercase(password):
    return any(char.islower() for char in password)

def _has_digits(password):
    return any(char.isdigit() for char in password)

def _has_special_chars(password):
    return any(not char.isalnum() for char in password)

def _has_no_spaces(password):
    return ' ' not in password

def _meets_length_requirements(password, min_length=8):
    return len(password) >= min_length if password else False

def validate_password(password, min_length=8):
    if not password:
        return False, "Password cannot be empty"

    validation_checks = [
        (_has_uppercase(password),
         "Password must contain at least one uppercase letter!"),
        (_has_lowercase(password),
         "Password must contain at least one lowercase letter!"),
        (_has_digits(password),
         "Password must contain at least one digit!"),
        (_has_special_chars(password),
         "Password must contain at least one special character!"),
        (_has_no_spaces(password),
         "Password cannot contain spaces!"),
        (_meets_length_requirements(password, min_length),
         f"Password must be at least {min_length} characters long!")
    ]

    failed_checks = [message for (is_valid, message) in validation_checks if not is_valid]

    if failed_checks:
        return False, "; ".join(failed_checks)

    return True, "Password is valid"