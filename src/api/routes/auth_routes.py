from flask import Blueprint, request, jsonify, current_app, g
from flask_smorest import Blueprint as SmorestBlueprint
from werkzeug.security import check_password_hash
from ..models.user_model import User, UserRole
from ..auth import token_required, admin_required, create_token
from ..db import db

blp = SmorestBlueprint('auth', __name__, url_prefix='/api/v1/auth')

DEFAULT_TOKEN_TYPE = "Bearer"
DEFAULT_TOKEN_TTL = 3600

def _auth_token_response(token: str, token_type: str = DEFAULT_TOKEN_TYPE, expires_in: int = DEFAULT_TOKEN_TTL, role: str | None = None):
    payload = {'token': token, 'token_type': token_type, 'expires_in': expires_in}
    if role is not None:
        payload['role'] = role
    return jsonify(payload)

@blp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json(silent=True)
    required_fields = ['email', 'password', 'first_name', 'last_name', 'phone']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    if db.query(User).filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    try:
        # Create new user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role=UserRole.GUEST,
            is_registered=True
        )
        user.set_password(data['password'])
        
        db.add(user)
        db.commit()
        
        # Generate auth token
        token = user.generate_auth_token()
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user.user_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'is_admin': user.role == UserRole.ADMIN
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        return jsonify({'message': 'Error registering user'}), 500

@blp.route('/create-admin', methods=['POST'])
@token_required
def create_admin():
    """Create admin user (only existing admins can create new admins)"""
    if not g.current_user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name', 'phone']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    if db.query(User).filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    try:
        # Create new admin user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role=UserRole.ADMIN,
            is_registered=True
        )
        user.set_password(data['password'])
        
        db.add(user)
        db.commit()
        
        return jsonify({
            'message': 'Admin user created successfully',
            'user': {
                'id': user.user_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'is_admin': user.role == UserRole.ADMIN
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        current_app.logger.error(f'Admin creation error: {str(e)}')
        return jsonify({'message': 'Error creating admin user'}), 500

@blp.route('/create-staff', methods=['POST'])
@token_required
def create_staff():
    """Create staff user (only admins can create staff)"""
    if not g.current_user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name', 'phone']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    if db.query(User).filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    try:
        # Create new staff user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role=UserRole.STAFF,
            is_registered=True
        )
        user.set_password(data['password'])
        
        db.add(user)
        db.commit()
        
        return jsonify({
            'message': 'Staff user created successfully',
            'user': {
                'id': user.user_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'is_admin': user.role == UserRole.ADMIN
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        current_app.logger.error(f'Staff creation error: {str(e)}')
        return jsonify({'message': 'Error creating staff user'}), 500

@blp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400
    
    user = db.query(User).filter_by(email=data['email'], is_registered=True).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    # Generate auth token
    token = user.generate_auth_token()
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user.user_id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.value,
            'is_admin': user.role == UserRole.ADMIN
        }
    })

@blp.route('/me')
@token_required
def get_current_user():
    """Get current user info"""
    role_value = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role
    is_admin = (role_value == 'ADMIN')
    return jsonify({
        'id': g.current_user.user_id,
        'email': g.current_user.email,
        'first_name': g.current_user.first_name,
        'last_name': g.current_user.last_name,
        'role': role_value,
        'is_admin': is_admin
    })

# Admin-only route example
@blp.route('/admin')
@token_required
@admin_required
def admin_only():
    """Example admin-only endpoint"""
    return jsonify({'message': 'Welcome admin!'})

@blp.route('/refresh')
@token_required
def refresh_token():
    role_value = g.current_user.role.value if hasattr(g.current_user.role, 'value') else g.current_user.role
    is_admin = (role_value == 'ADMIN')
    token = create_token(user_id=g.current_user.user_id, role=role_value, is_admin=is_admin)
    return _auth_token_response(token, role=role_value)
