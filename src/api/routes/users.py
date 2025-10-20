from flask.views import MethodView
from flask_smorest import Blueprint, abort
from src.api.schemas.user_schema import UserInSchema, UserOutSchema, UserPatchSchema
from src.api.services.user_service import (
    get_all_users,
    create_user,
    get_user_by_id,
    update_user_partial,
    update_user_full,
    delete_user
)

blp = Blueprint(
    "Users",
    "users",
    url_prefix="/api/v1/users",
    description="Operations on users (CRUD)."
)

@blp.route("/")
class UserList(MethodView):

    @blp.response(200, UserOutSchema(many=True), description="List all users.")
    def get(self):
        """Get all users"""
        try:
            return get_all_users()
        except Exception as e:
            abort(500, message=str(e))

    @blp.arguments(UserInSchema)
    @blp.response(201, UserOutSchema, description="User created successfully.")
    def post(self, new_user):
        """Create a new user"""
        try:
            result = create_user(new_user, via_booking=False)
            return result
        except ValueError as e:
            abort(400, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

@blp.route("/<int:user_id>")
class UserResource(MethodView):

    @blp.response(200, UserOutSchema, description="Get a single user by id.")
    def get(self, user_id):
        """Get a single user by ID"""
        user = get_user_by_id(user_id)
        if not user:
            abort(404, message="User not found")
        return user

    @blp.arguments(UserPatchSchema)
    @blp.response(200, UserOutSchema, description="Partially update a user")
    def patch(self, patch_data, user_id):
        """Partially update user fields"""
        try:
            user = update_user_partial(user_id, patch_data)
            if not user:
                abort(404, message="User not found")
            return user
        except ValueError as e:
            abort(400, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

    @blp.arguments(UserInSchema)
    @blp.response(200, UserOutSchema, description="Replace an existing user.")
    def put(self, updated_user, user_id):
        """Replace a user completely"""
        try:
            user = update_user_full(user_id, updated_user)
            if not user:
                abort(404, message="User not found")
            return user
        except ValueError as e:
            abort(400, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

    @blp.response(204, description="User deleted successfully")
    def delete(self, user_id):
        """Delete a user"""
        try:
            success = delete_user(user_id)
            if not success:
                abort(404, message="User not found")
            return "", 204
        except Exception as e:
            abort(500, message=str(e))