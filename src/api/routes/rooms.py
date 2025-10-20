from flask.views import MethodView
from flask_smorest import Blueprint, abort
from src.api.schemas.room_schema import (
    RoomInSchema, RoomOutSchema, RoomPatchSchema
)
from src.api.schemas.amenity_schema import (
    AmenityInSchema, AmenityOutSchema, AmenityPatchSchema
)
from src.api.services.room_service import (
    get_all_rooms,
    create_room,
    get_room_by_id,
    update_room_partial,
    update_room_full,
    delete_room
)

from src.api.services.amenity_service import (
    get_all_amenities,
    create_amenity,
    get_amenity_by_id,
    update_amenity,
    delete_amenity)

blp = Blueprint(
    "Rooms",
    "rooms",
    url_prefix="/api/v1/rooms",
    description="Operations on hotel rooms and amenities."
)


@blp.route("/")
class RoomList(MethodView):
    @blp.response(200, RoomOutSchema(many=True), description="List of all rooms in the hotel.")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all rooms"""
        try:
            result = get_all_rooms()
            return result
        except Exception as e:
            abort(500, message=str(e))

    @blp.arguments(RoomInSchema)
    @blp.response(201, RoomOutSchema, description="Room created successfully.")
    @blp.alt_response(400, description="Invalid room data provided")
    @blp.alt_response(409, description="Room with this number already exists")
    def post(self, new_room):
        """Create a new room"""
        try:
            result = create_room(new_room)
            return result
        except ValueError as e:
            abort(409, message=str(e))
        except Exception as e:
            abort(500, message=str(e))


@blp.route("/<int:room_id>")
class RoomResource(MethodView):

    @blp.response(200, RoomOutSchema, description="Room details retrieved successfully.")
    @blp.alt_response(404, description="Room not found")
    def get(self, room_id):
        """Get a single room by ID"""
        room = get_room_by_id(room_id)
        if not room:
            abort(404, message=f"Room with ID {room_id} not found")
        return room

    @blp.arguments(RoomPatchSchema)
    @blp.response(200, RoomOutSchema, description="Room updated successfully")
    @blp.alt_response(400, description="Invalid room data provided")
    @blp.alt_response(404, description="Room not found")
    @blp.alt_response(409, description="Room number conflict")
    def patch(self, patch_data, room_id):
        """Partially update room fields"""
        try:
            room = update_room_partial(room_id, patch_data)
            if not room:
                abort(404, message=f"Room with ID {room_id} not found")
            return room
        except ValueError as e:
            abort(409, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

    @blp.arguments(RoomInSchema)
    @blp.response(200, RoomOutSchema, description="Room replaced successfully.")
    @blp.alt_response(404, description="Room not found")
    @blp.alt_response(400, description="Invalid room data")
    @blp.alt_response(409, description="Room number conflict")
    def put(self, updated_room, room_id):
        """Replace a room completely"""
        try:
            room = update_room_full(room_id, updated_room)
            if not room:
                abort(404, message=f"Room with ID {room_id} not found")
            return room
        except ValueError as e:
            abort(409, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

    @blp.response(204, description="Room deleted successfully")
    @blp.alt_response(404, description="Room not found")
    def delete(self, room_id):
        """Delete a room"""
        try:
            success = delete_room(room_id)
            if not success:
                abort(404, message=f"Room with ID {room_id} not found")
            return "", 204
        except Exception as e:
            abort(500, message=str(e))


amenities_blp = Blueprint(
    "Amenities",
    "amenities",
    url_prefix="/api/v1/amenities",
    description="Operations on room amenities."
)


@amenities_blp.route("/")
class AmenityList(MethodView):
    @amenities_blp.response(200, AmenityOutSchema(many=True), description="List of all amenities.")
    @amenities_blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all amenities"""
        try:
            result = get_all_amenities()
            return result
        except Exception as e:
            abort(500, message=str(e))

    @amenities_blp.arguments(AmenityInSchema)
    @amenities_blp.response(201, AmenityOutSchema, description="Amenity created successfully.")
    @amenities_blp.alt_response(400, description="Invalid amenity data provided")
    @amenities_blp.alt_response(409, description="Amenity with this name already exists")
    def post(self, new_amenity):
        """Create a new amenity"""
        try:
            result = create_amenity(new_amenity)
            return result
        except ValueError as e:
            abort(409, message=str(e))
        except Exception as e:
            abort(500, message=str(e))


@amenities_blp.route("/<int:amenity_id>")
class AmenityResource(MethodView):

    @amenities_blp.response(200, AmenityOutSchema, description="Amenity details retrieved successfully.")
    @amenities_blp.alt_response(404, description="Amenity not found")
    def get(self, amenity_id):
        """Get a single amenity by ID"""
        amenity = get_amenity_by_id(amenity_id)
        if not amenity:
            abort(404, message=f"Amenity with ID {amenity_id} not found")
        return amenity

    @amenities_blp.arguments(AmenityPatchSchema)
    @amenities_blp.response(200, AmenityOutSchema, description="Amenity updated successfully")
    @amenities_blp.alt_response(400, description="Invalid amenity data provided")
    @amenities_blp.alt_response(404, description="Amenity not found")
    @amenities_blp.alt_response(409, description="Amenity name conflict")
    def patch(self, patch_data, amenity_id):
        """Partially update amenity fields"""
        try:
            amenity = update_amenity(amenity_id, patch_data)
            if not amenity:
                abort(404, message=f"Amenity with ID {amenity_id} not found")
            return amenity
        except ValueError as e:
            abort(409, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

    @amenities_blp.arguments(AmenityInSchema)
    @amenities_blp.response(200, AmenityOutSchema, description="Amenity replaced successfully.")
    @amenities_blp.alt_response(404, description="Amenity not found")
    @amenities_blp.alt_response(400, description="Invalid amenity data")
    @amenities_blp.alt_response(409, description="Amenity name conflict")
    def put(self, updated_amenity, amenity_id):
        """Replace an amenity completely"""
        try:
            amenity = update_amenity(amenity_id, updated_amenity)
            if not amenity:
                abort(404, message=f"Amenity with ID {amenity_id} not found")
            return amenity
        except ValueError as e:
            abort(409, message=str(e))
        except Exception as e:
            abort(500, message=str(e))

    @amenities_blp.response(204, description="Amenity deleted successfully")
    @amenities_blp.alt_response(404, description="Amenity not found")
    def delete(self, amenity_id):
        """Delete an amenity"""
        try:
            success = delete_amenity(amenity_id)
            if not success:
                abort(404, message=f"Amenity with ID {amenity_id} not found")
            return "", 204
        except Exception as e:
            abort(500, message=str(e))
