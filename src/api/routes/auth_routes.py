from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask import request, jsonify, current_app, g
from flask.views import MethodView
from flask_smorest import Blueprint as SmorestBlueprint, abort
from werkzeug.security import check_password_hash
from ..models.user_model import User, UserRole
from ..services.user_service import get_user_by_email, create_user, update_user_partial
from ..auth import token_required, admin_required, create_token, generate_auth_token_for_user
from ..db import db
import logging

logger = logging.getLogger(__name__)

blp = SmorestBlueprint('auth', __name__, url_prefix='/api/v1/auth')

DEFAULT_TOKEN_TYPE = "Bearer"
DEFAULT_TOKEN_TTL = 3600


def _get_role_value(user) -> str:
    """Extract role value from user object, handling both enum and string."""
    return user.role.value if hasattr(user.role, 'value') else user.role


def _auth_token_response(token: str, token_type: str = DEFAULT_TOKEN_TYPE, expires_in: int = DEFAULT_TOKEN_TTL,
                         role: str | None = None):
    payload = {'token': token, 'token_type': token_type, 'expires_in': expires_in}
    if role is not None:
        payload['role'] = role
    return jsonify(payload)


@blp.route('/register', methods=['POST'])
class Register(MethodView):  # <--- Змінено на MethodView
    """Register a new user or upgrade a guest user."""

    def post(self):
        data = request.get_json(silent=True)
        required_fields = ['email', 'password', 'first_name', 'last_name', 'phone']

        if not data:
            abort(400, message='No JSON data provided')

        if not all(field in data for field in required_fields):
            missing = [field for field in required_fields if field not in data]
            abort(400, message=f'Missing required fields: {", ".join(missing)}')

        if not isinstance(data['email'], str) or '@' not in data['email']:
            abort(400, message='Invalid email format')
        if not isinstance(data['password'], str) or len(data['password']) < 6:
            abort(400, message='Password must be at least 6 characters')

        email = (data['email'] or '').strip().lower()

        existing_user = get_user_by_email(db, email)

        if existing_user and existing_user.is_registered:
            abort(400, message="User with this email already exists.")

        try:
            user_data = {
                "email": email,
                "first_name": (data['first_name'] or '').strip(),
                "last_name": (data['last_name'] or '').strip(),
                "phone": (data['phone'] or '').strip(),
                "password": data['password'],
                "role": "GUEST"
            }

            if existing_user and not existing_user.is_registered:
                logger.info(f"Upgrading guest {email} to registered user.")
                user_data["is_registered"] = True
                user = update_user_partial(db, existing_user.user_id, user_data)

            else:
                logger.info(f"Creating new registered user {email}.")
                user = create_user(db, user_data, via_booking=False)

            if not user:
                raise Exception("User creation/update failed unexpectedly.")

            # Generate auth token
            token = generate_auth_token_for_user(user)

            return jsonify({
                'message': 'User registered successfully',
                'token': token,
                'user': user.to_dict()
            }), 201

        except IntegrityError as e:
            db.rollback()
            logger.warning(f'Database integrity error during registration: {e}')
            return jsonify({'message': 'User with this email or phone already exists'}), 409
        except ValueError as e:
            db.rollback()
            logger.warning(f'Validation error during registration: {e}')
            return jsonify({'message': str(e)}), 400
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception('Database error during registration')
            return jsonify({'message': 'Database error occurred'}), 500
        except Exception as e:
            db.rollback()
            logger.exception('Unexpected error during registration')
            return jsonify({'message': 'An unexpected error occurred'}), 500

@blp.route('/create-admin', methods=['POST'])
@token_required
def create_admin():
    """Create admin user (only existing admins can create new admins)"""
    if not g.current_user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description='Invalid or missing JSON')

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
    try:
        data = request.get_json(silent=True) or {}

        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        user = db.query(User).filter_by(email=email, is_registered=True).first()

        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid email or password'}), 401

        # Generate auth token
        token = generate_auth_token_for_user(user)

        role_value = _get_role_value(user)
        is_admin = (role_value == 'ADMIN')
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.user_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role_value,
                'is_admin': is_admin
            }
        })
    except Exception as e:
        current_app.logger.exception("Login error")
        return jsonify({'message': 'Internal server error during login'}), 500

@blp.route('/me')
@token_required
def get_current_user():
    """Get current user info"""
    role_value = _get_role_value(g.current_user)
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
    role_value = _get_role_value(g.current_user)
    is_admin = (role_value == 'ADMIN')
    token = create_token(user_id=g.current_user.user_id, role=role_value, is_admin=is_admin)
    return _auth_token_response(token, role=role_value)
