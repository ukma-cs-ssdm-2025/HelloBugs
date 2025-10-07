from flask.views import MethodView
from flask_smorest import Blueprint, abort
from ..schemas.booking_schema import BookingInSchema, BookingOutSchema
from datetime import datetime, timedelta
import secrets

blp = Blueprint(
    "Bookings",
    "bookings",
    url_prefix="/api/v1/bookings",
    description="Operations on room bookings (CRUD). Manage reservations, check availability, and handle booking lifecycle."
)

# mock data 
BOOKINGS = [
    {
        "booking_code": "BK001ABC",
        "user_id": 1,
        "guest_email": "john@example.com",
        "guest_first_name": "John",
        "guest_last_name": "Doe",
        "guest_phone": "+380501234567",
        "room_id": 3,
        "check_in_date": (datetime.now() + timedelta(days=5)).date(),
        "check_out_date": (datetime.now() + timedelta(days=8)).date(),
        "special_requests": "Late check-in, extra pillows",
        "status": "ACTIVE",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "booking_code": "BK002XYZ",
        "user_id": None,
        "guest_email": "guest@example.com",
        "guest_first_name": "Jane",
        "guest_last_name": "Smith",
        "guest_phone": "+380509876543",
        "room_id": 2,
        "check_in_date": (datetime.now() - timedelta(days=3)).date(),
        "check_out_date": (datetime.now() - timedelta(days=1)).date(),
        "special_requests": None,
        "status": "COMPLETED",
        "created_at": datetime.now() - timedelta(days=10),
        "updated_at": datetime.now() - timedelta(days=1)
    }
]

def generate_booking_code():
    """Generate a unique booking code"""
    return f"BK{secrets.randbelow(1000):03d}{secrets.token_hex(3).upper()}"

@blp.route("/")
class BookingList(MethodView):

    @blp.response(200, BookingOutSchema(many=True), description="List of all bookings.")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all bookings
        
        Returns a complete list of all bookings in the system.
        For customers: returns only their own bookings.
        For staff/admin: returns all bookings.
        """
        return BOOKINGS

    @blp.arguments(BookingInSchema)
    @blp.response(201, BookingOutSchema, description="Booking created successfully.")
    @blp.alt_response(400, description="Invalid booking data provided")
    @blp.alt_response(409, description="Room not available for selected dates")
    @blp.alt_response(404, description="Room or user not found")
    def post(self, new_booking):
        """Create a new booking
        
        Creates a new room booking for the specified dates.
        Automatically generates a unique booking code.
        Validates room availability and date ranges.
        """
        new_booking = dict(new_booking)
        
        check_in = new_booking["check_in_date"]
        check_out = new_booking["check_out_date"]
        
        if check_in >= check_out:
            abort(400, message="Check-out date must be after check-in date")
        
        if check_in < datetime.now().date():
            abort(400, message="Check-in date cannot be in the past")
        
        room_id = new_booking["room_id"]
        overlapping = [
            b for b in BOOKINGS 
            if b["room_id"] == room_id 
            and b["status"] == "ACTIVE"
            and not (check_out <= b["check_in_date"] or check_in >= b["check_out_date"])
        ]
        
        if overlapping:
            abort(409, message=f"Room {room_id} is not available for the selected dates")
        
        new_booking["booking_code"] = generate_booking_code()
        new_booking["status"] = "ACTIVE"
        new_booking["created_at"] = datetime.now()
        new_booking["updated_at"] = datetime.now()
        
        BOOKINGS.append(new_booking)
        return new_booking

@blp.route("/<string:booking_code>")
class BookingResource(MethodView):

    @blp.response(200, BookingOutSchema, description="Booking details retrieved successfully.")
    @blp.alt_response(404, description="Booking not found")
    @blp.alt_response(403, description="Access denied to this booking")
    def get(self, booking_code):
        """Get a single booking by code"""
        booking = next((b for b in BOOKINGS if b["booking_code"] == booking_code), None)
        if not booking:
            abort(404, message=f"Booking with code {booking_code} not found")
        return booking