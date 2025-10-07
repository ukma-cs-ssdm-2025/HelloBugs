from flask.views import MethodView
from flask_smorest import Blueprint, abort
from ..schemas.room_schema import RoomInSchema, RoomOutSchema
from datetime import datetime

blp = Blueprint(
    "Rooms",
    "rooms",
    url_prefix="/api/v1/rooms",
    description="Operations on hotel rooms (CRUD). Manage room inventory, types, pricing and availability."
)

# mock data
ROOMS = [
    {
        "id": 1,
        "room_number": "101",
        "room_type": "ECONOMY",
        "max_guest": 2,
        "base_price": 80.0,
        "status": "AVAILABLE",
        "description": "Cozy economy room with essential amenities",
        "floor": 1,
        "size_sqm": 18.0,
        "main_photo_url": "https://example.com/rooms/101-main.jpg",
        "photo_urls": ["https://example.com/rooms/101-1.jpg", "https://example.com/rooms/101-2.jpg"]
    },
    {
        "id": 2,
        "room_number": "201",
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 120.0,
        "status": "AVAILABLE",
        "description": "Comfortable standard room with city view",
        "floor": 2,
        "size_sqm": 25.0,
        "main_photo_url": "https://example.com/rooms/201-main.jpg",
        "photo_urls": ["https://example.com/rooms/201-1.jpg"]
    },
    {
        "id": 3,
        "room_number": "301",
        "room_type": "DELUXE",
        "max_guest": 4,
        "base_price": 200.0,
        "status": "OCCUPIED",
        "description": "Spacious deluxe suite with premium amenities",
        "floor": 3,
        "size_sqm": 40.0,
        "main_photo_url": "https://example.com/rooms/301-main.jpg",
        "photo_urls": ["https://example.com/rooms/301-1.jpg", "https://example.com/rooms/301-2.jpg", "https://example.com/rooms/301-3.jpg"]
    }
]

@blp.route("/")
class RoomList(MethodView):

    @blp.response(200, RoomOutSchema(many=True), description="List of all rooms in the hotel.")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all rooms
        
        Returns a complete list of all rooms in the hotel system with their details,
        including availability status, pricing, and amenities.
        """
        return ROOMS

    @blp.arguments(RoomInSchema)
    @blp.response(201, RoomOutSchema, description="Room created successfully.")
    @blp.alt_response(400, description="Invalid room data provided")
    @blp.alt_response(409, description="Room with this number already exists")
    def post(self, new_room):
        """Create a new room
        
        Admin operation to add a new room to the hotel inventory.
        Requires authentication with ADMIN role.
        """
        new_room = dict(new_room)
        
        if any(r["room_number"] == new_room["room_number"] for r in ROOMS):
            abort(409, message=f"Room with number {new_room['room_number']} already exists")
        
        new_room.pop("id", None)
        new_room["id"] = max((r["id"] for r in ROOMS), default=0) + 1
        ROOMS.append(new_room)
        return new_room

@blp.route("/<int:room_id>")
class RoomResource(MethodView):

    @blp.response(200, RoomOutSchema, description="Room details retrieved successfully.")
    @blp.alt_response(404, description="Room not found")
    def get(self, room_id):
        """Get a single room by ID
        
        Retrieve detailed information about a specific room including all amenities,
        photos, and current availability status.
        """
        room = next((r for r in ROOMS if r["id"] == room_id), None)
        if not room:
            abort(404, message=f"Room with ID {room_id} not found")
        return room