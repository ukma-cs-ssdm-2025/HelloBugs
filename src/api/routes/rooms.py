from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from datetime import date, timedelta
import logging
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
from src.api.services.booking_service import get_room_booked_ranges
from src.api.services.amenity_service import (
    get_all_amenities,
    create_amenity,
    get_amenity_by_id,
    update_amenity,
    delete_amenity
)
from src.api.db import db
from src.api.models.room_model import Room, RoomType, RoomStatus
from src.api.models.booking_model import Booking, BookingStatus

logger = logging.getLogger(__name__)

blp = Blueprint(
    "Rooms",
    "rooms",
    url_prefix="/api/v1/rooms",
    description="Operations on hotel rooms"
)


@blp.route("/")
class RoomList(MethodView):
    @blp.response(200, RoomOutSchema(many=True), description="List of all rooms")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get rooms. If query params provided, apply server-side filtering.
        Query params (optional):
          - check_in: YYYY-MM-DD
          - check_out: YYYY-MM-DD (must be after check_in)
          - room_type: ECONOMY|STANDARD|DELUXE
          - min_price: float
          - max_price: float
          - guests: int
        """
        try:
            check_in_str = request.args.get("check_in")
            check_out_str = request.args.get("check_out")

            room_type = request.args.get("room_type")
            min_price = request.args.get("min_price", type=float)
            max_price = request.args.get("max_price", type=float)
            guests = request.args.get("guests", type=int)

            if not any([check_in_str, check_out_str, room_type, min_price is not None, max_price is not None, guests]):
                return get_all_rooms(db)

            check_in_date = None
            check_out_date = None
            if check_in_str or check_out_str:
                if not (check_in_str and check_out_str):
                    abort(400, message="Both 'check_in' and 'check_out' are required when filtering by dates")
                try:
                    check_in_date = date.fromisoformat(check_in_str)
                    check_out_date = date.fromisoformat(check_out_str)
                except ValueError:
                    abort(400, message="Invalid date format. Use YYYY-MM-DD")
                if check_out_date <= check_in_date:
                    abort(400, message="'check_out' must be after 'check_in'")

            query = db.query(Room)
            if room_type:
                try:
                    rt = RoomType[room_type]
                except KeyError:
                    abort(400, message=f"Invalid room_type: {room_type}")
                query = query.filter(Room.room_type == rt)
            if min_price is not None:
                query = query.filter(Room.base_price >= min_price)
            if max_price is not None:
                query = query.filter(Room.base_price <= max_price)
            if guests:
                query = query.filter(Room.max_guest >= guests)

            candidates = query.all()

            if check_in_date and check_out_date:
                overlapping = db.query(Booking.room_id).filter(
                    Booking.status != BookingStatus.CANCELLED,
                    ~(((Booking.check_out_date <= check_in_date)) | ((Booking.check_in_date >= check_out_date)))
                ).distinct().all()
                occupied_room_ids = {rid for (rid,) in overlapping}
                available = [room for room in candidates if room.room_id not in occupied_room_ids]
                return available

            return candidates
        except Exception as e:
            logger.error(f"Error getting rooms: {e}")
            raise e

    @blp.arguments(RoomInSchema)
    @blp.response(201, RoomOutSchema, description="Room created successfully")
    @blp.alt_response(400, description="Invalid room data")
    @blp.alt_response(409, description="Room with this number already exists")
    def post(self, new_room):
        """Create a new room"""
        try:
            result = create_room(db, new_room)
            return result
        except ValueError as e:
            abort(409, message=str(e))


@blp.route("/<int:room_id>")
class RoomResource(MethodView):

    @blp.response(200, RoomOutSchema, description="Room details retrieved successfully")
    @blp.alt_response(404, description="Room not found")
    def get(self, room_id):
        """Get a single room by ID"""
        room = get_room_by_id(db, room_id)
        if not room:
            abort(404, message=f"Room with ID {room_id} not found")
        return room

    @blp.arguments(RoomPatchSchema)
    @blp.response(200, RoomOutSchema, description="Room updated successfully")
    @blp.alt_response(400, description="Invalid room data")
    @blp.alt_response(404, description="Room not found")
    @blp.alt_response(409, description="Room number conflict")
    def patch(self, patch_data, room_id):
        """Partially update room fields"""
        try:
            room = update_room_partial(db, room_id, patch_data)
            if not room:
                abort(404, message=f"Room with ID {room_id} not found")
            return room
        except ValueError as e:
            abort(409, message=str(e))

    @blp.arguments(RoomInSchema)
    @blp.response(200, RoomOutSchema, description="Room replaced successfully")
    @blp.alt_response(404, description="Room not found")
    @blp.alt_response(400, description="Invalid room data")
    @blp.alt_response(409, description="Room number conflict")
    def put(self, updated_room, room_id):
        """Replace a room completely"""
        try:
            room = update_room_full(db, room_id, updated_room)
            if not room:
                abort(404, message=f"Room with ID {room_id} not found")
            return room
        except ValueError as e:
            abort(409, message=str(e))

    @blp.response(204, description="Room deleted successfully")
    @blp.alt_response(404, description="Room not found")
    @blp.alt_response(400, description="Invalid request")
    def delete(self, room_id):
        """Delete a room"""
        success = delete_room(db, room_id)
        if not success:
            abort(404, message=f"Room with ID {room_id} not found")
        return "", 204


@blp.route("/<int:room_id>/availability")
class RoomAvailability(MethodView):
    @blp.alt_response(404, description="Room not found")
    def get(self, room_id):
        """Get booked date ranges for a room within a window.
        Query params:
        - start: YYYY-MM-DD (default: today)
        - end: YYYY-MM-DD (default: today + 90 days)
        """
        room = get_room_by_id(db, room_id)
        if not room:
            abort(404, message=f"Room with ID {room_id} not found")

        start_str = request.args.get("start")
        end_str = request.args.get("end")
        today = date.today()
        try:
            start_date = date.fromisoformat(start_str) if start_str else today
        except ValueError:
            start_date = today
        try:
            end_date = date.fromisoformat(end_str) if end_str else (today + timedelta(days=90))
        except ValueError:
            end_date = today + timedelta(days=90)

        if end_date <= start_date:
            end_date = start_date + timedelta(days=1)

        booked = get_room_booked_ranges(db, room_id, start_date, end_date)
        return {
            "room_id": room_id,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "booked": booked
        }


amenities_blp = Blueprint(
    "Amenities",
    "amenities",
    url_prefix="/api/v1/amenities",
    description="Operations on room amenities"
)


@amenities_blp.route("/")
class AmenityList(MethodView):
    @amenities_blp.response(200, AmenityOutSchema(many=True), description="List of all amenities")
    @amenities_blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all amenities"""
        result = get_all_amenities(db)
        return result

    @amenities_blp.arguments(AmenityInSchema)
    @amenities_blp.response(201, AmenityOutSchema, description="Amenity created successfully")
    @amenities_blp.alt_response(400, description="Invalid amenity data")
    @amenities_blp.alt_response(409, description="Amenity with this name already exists")
    def post(self, new_amenity):
        """Create a new amenity"""
        try:
            result = create_amenity(db, new_amenity)
            return result
        except ValueError as e:
            abort(409, message=str(e))


@amenities_blp.route("/<int:amenity_id>")
class AmenityResource(MethodView):

    @amenities_blp.response(200, AmenityOutSchema, description="Amenity details retrieved successfully")
    @amenities_blp.alt_response(404, description="Amenity not found")
    def get(self, amenity_id):
        """Get a single amenity by ID"""
        amenity = get_amenity_by_id(db, amenity_id)
        if not amenity:
            abort(404, message=f"Amenity with ID {amenity_id} not found")
        return amenity

    @amenities_blp.arguments(AmenityPatchSchema)
    @amenities_blp.response(200, AmenityOutSchema, description="Amenity updated successfully")
    @blp.alt_response(400, description="Invalid amenity data")
    @blp.alt_response(404, description="Amenity not found")
    @blp.alt_response(409, description="Amenity name conflict")
    def patch(self, patch_data, amenity_id):
        """Partially update amenity fields"""
        try:
            amenity = update_amenity(db, amenity_id, patch_data)
            if not amenity:
                abort(404, message=f"Amenity with ID {amenity_id} not found")
            return amenity
        except ValueError as e:
            abort(409, message=str(e))

    @amenities_blp.arguments(AmenityInSchema)
    @amenities_blp.response(200, AmenityOutSchema, description="Amenity replaced successfully")
    @blp.alt_response(404, description="Amenity not found")
    @blp.alt_response(400, description="Invalid amenity data")
    @blp.alt_response(409, description="Amenity name conflict")
    def put(self, updated_amenity, amenity_id):
        """Replace an amenity completely"""
        try:
            amenity = update_amenity(db, amenity_id, updated_amenity)
            if not amenity:
                abort(404, message=f"Amenity with ID {amenity_id} not found")
            return amenity
        except ValueError as e:
            abort(409, message=str(e))

    @amenities_blp.response(204, description="Amenity deleted successfully")
    @blp.alt_response(404, description="Amenity not found")
    def delete(self, amenity_id):
        """Delete an amenity"""
        success = delete_amenity(db, amenity_id)
        if not success:
            abort(404, message=f"Amenity with ID {amenity_id} not found")
        return "", 204


# FR-011: Calendar of room occupancy (booked ranges)
@blp.route("/<int:room_id>/booked-ranges")
class RoomBookedRanges(MethodView):
    def get(self, room_id: int):
        """Get booked date ranges for a room within [start, end].
        Query params:
          - start: YYYY-MM-DD (optional, default=today)
          - end: YYYY-MM-DD (optional, default=today+30 days)
        Returns list of {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}.
        """
        try:
            start_str = request.args.get("start")
            end_str = request.args.get("end")

            start_date = date.today() if not start_str else date.fromisoformat(start_str)
            end_date = (start_date + timedelta(days=30)) if not end_str else date.fromisoformat(end_str)

            if end_date <= start_date:
                abort(400, message="'end' must be after 'start'")

            ranges = get_room_booked_ranges(db, room_id, start_date, end_date)
            return ranges
        except ValueError:
            abort(400, message="Invalid date format. Use YYYY-MM-DD")