from flask.views import MethodView
from flask_smorest import Blueprint, abort
from api.schemas.user_schema import UserInSchema, UserOutSchema, UserPatchSchema, UserRole
from datetime import datetime
from flask import current_app

blp = Blueprint(
    "Users",
    "users",
    url_prefix="/api/v1/users",
    description="Operations on users (CRUD)."
)

# mock data
USERS = [
    {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "hashed_password_123",
        "phone": "+380501234567",
        "role": "CUSTOMER",
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com",
        "password": "hashed_password_456",
        "phone": "+380509876543",
        "role": "STAFF",
        "created_at": datetime.now()
    },
]

@blp.route("/")
class UserList(MethodView):

    @blp.response(200, UserOutSchema(many=True), description="List all users.")
    def get(self):
        """Get all users"""
        return USERS

    @blp.arguments(UserInSchema)
    @blp.response(201, UserOutSchema, description="User created successfully.")
    def post(self, new_user):
        """Create a new user"""
        new_user = dict(new_user)
        new_user.pop("id", None)
        new_user["id"] = max((u["id"] for u in USERS), default=0) + 1
        new_user["created_at"] = datetime.now()
        USERS.append(new_user)
        return new_user
    

@blp.route("/<int:user_id>")
class UserResource(MethodView):

    @blp.response(200, UserOutSchema, description="Get a single user by id.")
    def get(self, user_id):
        """Get a single user"""
        user = next((u for u in USERS if u["id"] == user_id), None)
        if not user:
            abort(404, message="User not found")
        return user

