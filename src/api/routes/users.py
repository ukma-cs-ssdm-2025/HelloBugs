from flask.views import MethodView
from flask_smorest import Blueprint, abort
from src.api.schemas.user_schema import UserInSchema, UserOutSchema, UserPatchSchema, UserRole
from src.api.models.user_model import User
from src.api.db import db
from src.api.auth import token_required, admin_required
from datetime import datetime
from flask import current_app

blp = Blueprint(
    "Users",
    "users",
    url_prefix="/api/v1/users",
    description="Operations on users (CRUD)."
)

@blp.route("/")
class UserList(MethodView):

    @token_required
    @admin_required
    @blp.response(200, UserOutSchema(many=True), description="List all users.")
    def get(self):
        """Get all users
        
        Returns a complete list of all registered users in the system.
        For admin users: returns all accounts including staff and customers.
        For regular users: access is restricted.
        """
        users = db.query(User).all()
        return [
            {
                "id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role.value if user.role else "GUEST",
                "created_at": user.created_at
            }
            for user in users
        ]

    @token_required
    @admin_required
    @blp.arguments(UserInSchema)
    @blp.response(201, UserOutSchema, description="User created successfully.")
    def post(self, new_user):
        """Create a new user
        
        Creates a new user account with the provided data.
        Automatically assigns a unique ID and creation timestamp.
        Performs basic validation on input fields such as email, role, and password.
        May reject duplicate usernames or emails to maintain uniqueness.
        """
        # Перевіряємо, чи email вже існує
        existing_user = db.query(User).filter_by(email=new_user['email']).first()
        if existing_user:
            abort(400, message="User with this email already exists")
        
        # Створюємо нового користувача
        user = User(
            email=new_user['email'],
            first_name=new_user['first_name'],
            last_name=new_user['last_name'],
            phone=new_user['phone'],
            role=UserRole[new_user.get('role', 'GUEST')],
            is_registered=True
        )
        
        # Хешуємо пароль
        if 'password' in new_user:
            user.set_password(new_user['password'])
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role.value,
            "created_at": user.created_at
        }

@blp.route("/<int:user_id>")
class UserResource(MethodView):

    @token_required
    @blp.response(200, UserOutSchema, description="Get a single user by id.")
    def get(self, user_id):
        """Get a single user by ID
        
        Retrieve detailed information about a specific user by their unique ID.
        Includes personal information such as username, email, role, and account creation date.
        Returns a 404 error if the user with the given ID does not exist.
        """
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            abort(404, message="User not found")
        
        return {
            "id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role.value if user.role else "GUEST",
            "created_at": user.created_at
        }

    @token_required
    @admin_required
    @blp.arguments(UserPatchSchema)
    @blp.response(200, UserOutSchema, description="Partially update a user")
    @blp.alt_response(400, description="Invalid user data provided")
    @blp.alt_response(404, description="User not found")
    def patch(self, patch_data, user_id):
        """Partially update user fields

        This endpoint allows a user to update some of their profile information.
        Accessible to the user through their account.
        """
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            abort(404, message="User not found")
        
        # Оновлюємо поля
        for key, value in patch_data.items():
            if key == 'password':
                user.set_password(value)
            elif key == 'role':
                user.role = UserRole[value]
            elif hasattr(user, key):
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        return {
            "id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role.value if user.role else "GUEST",
            "created_at": user.created_at
        }

    @token_required
    @admin_required
    @blp.arguments(UserInSchema)
    @blp.response(200, UserOutSchema, description="Replace an existing user.")
    def put(self, updated_user, user_id):
        """Replace a user completely
        
        Replace all information of an existing user identified by user_id
        with the provided data. The user's ID and creation date remain unchanged.
        Returns a 404 error if the user does not exist.
        """
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            abort(404, message="User not found")
        
        # Оновлюємо всі поля
        user.email = updated_user['email']
        user.first_name = updated_user['first_name']
        user.last_name = updated_user['last_name']
        user.phone = updated_user['phone']
        user.role = UserRole[updated_user.get('role', 'GUEST')]
        
        if 'password' in updated_user:
            user.set_password(updated_user['password'])
        
        db.commit()
        db.refresh(user)
        
        return {
            "id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role.value,
            "created_at": user.created_at
        }

    @token_required
    @admin_required
    @blp.response(204, description="User deleted successfully")
    @blp.alt_response(404, description="User not found")
    def delete(self, user_id):
        """Delete a user
        
        Removes a user from the system by their ID.
        Returns 204 No Content on success.
        """
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            abort(404, message=f"User with ID {user_id} not found")
        
        db.delete(user)
        db.commit()
        return "", 204