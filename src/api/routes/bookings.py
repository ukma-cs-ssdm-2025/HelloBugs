from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import g
from src.api.auth import token_optional
from src.api.schemas.booking_schema import (
    BookingInSchema, BookingOutSchema, BookingPatchSchema
)
from src.api.services.booking_service import (
    get_all_bookings,
    create_booking,
    get_booking_by_code,
    update_booking_partial,
    update_booking_full,
    cancel_booking,
    get_user_bookings,
    get_upcoming_checkins
)
from src.api.db import db

blp = Blueprint(
    "Bookings",
    "bookings",
    url_prefix="/api/v1/bookings",
    description="Operations on room bookings (CRUD). Manage reservations, check availability, and handle booking lifecycle."
)


@blp.route("/")
class BookingList(MethodView):

    @blp.response(200, BookingOutSchema(many=True), description="List of all bookings.")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all bookings"""
        try:
            return get_all_bookings(db)
        except Exception as e:
            abort(500, message=str(e))

    @blp.arguments(BookingInSchema)
    @blp.response(201, BookingOutSchema, description="Booking created successfully.")
    @blp.alt_response(400, description="Invalid booking data provided")
    @blp.alt_response(409, description="Room not available for selected dates")
    @blp.alt_response(404, description="Room or user not found")
    @token_optional
    def post(self, new_booking):
        """Create a new booking"""
        current_user = getattr(g, 'current_user', None)
        if current_user:
            new_booking['user_id'] = current_user.user_id

        try:
            booking = create_booking(db, new_booking)
            db.commit()
            return booking
        except ValueError as e:
            db.rollback()
            if "not available" in str(e).lower():
                abort(409, message=str(e))
            elif "not found" in str(e).lower():
                abort(404, message=str(e))
            else:
                abort(400, message=str(e))
        except Exception as e:
            db.rollback()
            abort(500, message=str(e))


@blp.route("/user/<int:user_id>")
class UserBookings(MethodView):

    @blp.response(200, BookingOutSchema(many=True), description="User bookings")
    @blp.alt_response(500, description="Internal server error")
    def get(self, user_id):
        try:
            return get_user_bookings(db, user_id)
        except Exception as e:
            abort(500, message=str(e))


@blp.route("/upcoming-checkins")
class UpcomingCheckins(MethodView):

    @blp.response(200, BookingOutSchema(many=True), description="Upcoming check-ins")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        try:
            return get_upcoming_checkins(db)
        except Exception as e:
            abort(500, message=str(e))


@blp.route("/<string:booking_code>")
class BookingResource(MethodView):

    @blp.response(200, BookingOutSchema, description="Booking details retrieved successfully.")
    @blp.alt_response(404, description="Booking not found")
    def get(self, booking_code):
        booking = get_booking_by_code(db, booking_code)
        if not booking:
            abort(404, message=f"Booking with code {booking_code} not found")
        return booking

    @blp.arguments(BookingPatchSchema)
    @blp.response(200, BookingOutSchema, description="Booking updated successfully")
    @blp.alt_response(400, description="Invalid booking data provided")
    @blp.alt_response(403, description="Cannot modify completed/cancelled booking")
    @blp.alt_response(404, description="Booking not found")
    @blp.alt_response(409, description="Room not available for new dates")
    def patch(self, patch_data, booking_code):
        try:
            booking = update_booking_partial(db, booking_code, patch_data)
            if not booking:
                abort(404, message=f"Booking with code {booking_code} not found")
            db.commit()
            return booking
        except ValueError as e:
            db.rollback()
            if "cannot modify" in str(e).lower():
                abort(403, message=str(e))
            elif "not available" in str(e).lower():
                abort(409, message=str(e))
            else:
                abort(400, message=str(e))
        except Exception as e:
            db.rollback()
            abort(500, message=str(e))

    @blp.arguments(BookingInSchema)
    @blp.response(200, BookingOutSchema, description="Booking replaced successfully.")
    @blp.alt_response(404, description="Booking not found")
    @blp.alt_response(400, description="Invalid booking data")
    @blp.alt_response(403, description="Cannot modify completed/cancelled booking")
    @blp.alt_response(409, description="Room not available for new dates")
    def put(self, updated_booking, booking_code):
        try:
            booking = update_booking_full(db, booking_code, updated_booking)
            if not booking:
                abort(404, message=f"Booking with code {booking_code} not found")
            db.commit()
            return booking
        except ValueError as e:
            db.rollback()
            if "cannot modify" in str(e).lower():
                abort(403, message=str(e))
            elif "not available" in str(e).lower():
                abort(409, message=str(e))
            else:
                abort(400, message=str(e))
        except Exception as e:
            db.rollback()
            abort(500, message=str(e))

    @blp.response(204, description="Booking cancelled successfully")
    @blp.alt_response(404, description="Booking not found")
    def delete(self, booking_code):
        try:
            success = cancel_booking(db, booking_code)
            if not success:
                abort(404, message=f"Booking with code {booking_code} not found")
            db.commit()
            return "", 204
        except Exception as e:
            db.rollback()
            abort(500, message=str(e))
