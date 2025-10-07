from flask.views import MethodView
from flask_smorest import Blueprint, abort
from src.api.schemas.user_schema import UserInSchema, UserOutSchema, UserPatchSchema, UserRole
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
        """Get all users
        
        Returns a complete list of all registered users in the system.
        For admin users: returns all accounts including staff and customers.
        For regular users: access is restricted.
        """
        return USERS

    @blp.arguments(UserInSchema)
    @blp.response(201, UserOutSchema, description="User created successfully.")
    def post(self, new_user):
        """Create a new user
        
        Creates a new user account with the provided data.
        Automatically assigns a unique ID and creation timestamp.
        Performs basic validation on input fields such as email, role, and password.
        May reject duplicate usernames or emails to maintain uniqueness.
        """
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
        """Get a single user by ID
        
        Retrieve detailed information about a specific user by their unique ID.
        Includes personal information such as username, email, role, and account creation date.
        Returns a 404 error if the user with the given ID does not exist.
        """
        user = next((u for u in USERS if u["id"] == user_id), None)
        if not user:
            abort(404, message="User not found")
        return user


    @blp.arguments(UserPatchSchema)
    @blp.response(200, UserOutSchema, description="Partially update a user")
    @blp.alt_response(400, description="Invalid user data provided")
    @blp.alt_response(404, description="User not found")
    def patch(self, patch_data, user_id):
        """ Partially update user fields

        This endpoint allows a user to update some of their profile information.
        Accessible to the user through their account.
        """
        user = next((u for u in USERS if u["id"] == user_id), None)
        if not user:
            abort(404, message="User not found")
        for k, v in patch_data.items():
            if k in ("id", "created_at"):
                continue
            user[k] = v
        return user


