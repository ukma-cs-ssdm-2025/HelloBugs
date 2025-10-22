from src.api.db import db
from src.api.models.booking_model import Booking, BookingStatus
from src.api.models.room_model import Room, RoomStatus
from src.api.models.user_model import User
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_, not_
from datetime import datetime, date, timedelta
import logging
import time
import random

logger = logging.getLogger(__name__)


def generate_booking_code():
    timestamp = int(time.time() * 1000) % 1000000
    random_part = random.randint(10000, 99999)
    return f"BK{timestamp}{random_part}"


def check_room_availability(room_id, check_in, check_out, exclude_booking_code=None):
    try:
        room = db.query(Room).get(room_id)
        if not room or room.status != RoomStatus.AVAILABLE:
            return False, "Room is not available"

        overlapping_query = db.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status == BookingStatus.ACTIVE,
            not_(or_(
                check_out <= Booking.check_in_date,
                check_in >= Booking.check_out_date
            ))
        )

        if exclude_booking_code:
            overlapping_query = overlapping_query.filter(Booking.booking_code != exclude_booking_code)

        overlapping_bookings = overlapping_query.count()

        if overlapping_bookings > 0:
            return False, "Room is already booked for these dates"

        return True, "Room is available"

    except SQLAlchemyError as e:
        logger.error(f"Database error checking room availability: {e}")
        return False, "Database error"


def calculate_total_price(room_id, check_in, check_out):
    try:
        room = db.query(Room).get(room_id)
        if not room:
            return 0

        nights = (check_out - check_in).days
        return float(room.base_price) * nights

    except Exception as e:
        logger.error(f"Error calculating total price: {e}")
        return 0


def get_all_bookings():
    try:
        bookings = db.query(Booking).all()
        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching bookings: {e}")
        raise Exception(f"Database error: {e}")


def get_booking_by_code(booking_code):
    try:
        booking = db.query(Booking).get(booking_code)
        return booking
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching booking {booking_code}: {e}")
        raise Exception(f"Database error: {e}")


def get_user_bookings(user_id):
    try:
        bookings = db.query(Booking).filter_by(user_id=user_id).all()
        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching user bookings {user_id}: {e}")
        raise Exception(f"Database error: {e}")


def create_booking(data):
    booking_code = None
    try:
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')

        if check_in >= check_out:
            raise ValueError("Check-out date must be after check-in date")

        if check_in < date.today():
            raise ValueError("Check-in date cannot be in the past")

        room_id = data.get('room_id')
        is_available, message = check_room_availability(room_id, check_in, check_out)

        if not is_available:
            raise ValueError(message)

        user_id = data.get('user_id')
        email = data.get('email')

        if user_id:
            user = db.query(User).get(user_id)
            if not user:
                raise ValueError("User not found")
        elif email:
            existing_user = db.query(User).filter_by(email=email).first()
            if existing_user:
                if existing_user.is_registered:
                    raise ValueError("This email is already registered. Please log in to make a booking.")
                else:
                    pass

            new_guest = User(
                email=email,
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                phone=data.get('phone'),
                is_registered=False,
                created_at=datetime.now()
            )
            db.add(new_guest)
            db.flush()
            user_id = new_guest.user_id
        else:
            raise ValueError("Either user_id or email must be provided")

        if not user_id:
            raise ValueError("Could not determine user_id")

        room = db.query(Room).get(room_id)
        if not room:
            raise ValueError("Room not found")

        booking_code = generate_booking_code()

        new_booking = Booking(
            booking_code=booking_code,
            user_id=user_id,
            room_id=room_id,
            check_in_date=check_in,
            check_out_date=check_out,
            special_requests=data.get('special_requests'),
            status=data.get('status', BookingStatus.ACTIVE),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(new_booking)
        db.commit()

        return new_booking

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating booking: {e}")

        error_msg = str(e)

        if "email" in error_msg.lower() or "ix_users_email" in error_msg:
            raise ValueError("This email is already registered. Please log in or use a different email.")

        elif "booking_code" in error_msg.lower():
            logger.error(f"Duplicate booking code: {booking_code}")
            raise ValueError("System error - please try again")

        else:
            raise ValueError("Database error - please try again")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating booking: {e}")
        raise Exception(f"Database error: {e}")
    except ValueError as e:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating booking: {e}")
        raise


def update_booking_partial(booking_code, data):
    try:
        booking = db.query(Booking).get(booking_code)
        if not booking:
            return None

        # Для завершених або скасованих бронювань дозволяємо змінювати тільки статус
        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            allowed_fields = {'status'}
            if set(data.keys()) - allowed_fields:
                raise ValueError("Can only change status for completed/cancelled bookings")

        # Перевірити доступність кімнати при зміні дат або кімнати
        check_in = data.get('check_in_date', booking.check_in_date)
        check_out = data.get('check_out_date', booking.check_out_date)
        room_id = data.get('room_id', booking.room_id)

        if 'check_in_date' in data or 'check_out_date' in data or 'room_id' in data:
            is_available, message = check_room_availability(
                room_id, check_in, check_out, booking_code
            )
            if not is_available:
                raise ValueError(message)

        for key, value in data.items():
            if hasattr(booking, key) and key not in ['booking_code', 'created_at']:
                setattr(booking, key, value)

        booking.updated_at = datetime.utcnow()
        db.commit()
        return booking

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error updating booking {booking_code}: {e}")
        raise ValueError("Update conflict")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating booking {booking_code}: {e}")
        raise Exception(f"Database error: {e}")
    except ValueError as e:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating booking {booking_code}: {e}")
        raise


def update_booking_full(booking_code, data):
    try:
        booking = db.query(Booking).get(booking_code)
        if not booking:
            return None

        # Не дозволяємо змінювати завершені або скасовані бронювання
        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise ValueError("Cannot modify completed or cancelled bookings")

        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        room_id = data.get('room_id')

        is_available, message = check_room_availability(
            room_id, check_in, check_out, booking_code
        )
        if not is_available:
            raise ValueError(message)

        booking.user_id = data.get('user_id')
        booking.room_id = data.get('room_id')
        booking.check_in_date = check_in
        booking.check_out_date = check_out
        booking.special_requests = data.get('special_requests')
        booking.updated_at = datetime.now()

        db.commit()
        return booking

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error updating booking {booking_code}: {e}")
        raise ValueError("Update conflict")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating booking {booking_code}: {e}")
        raise Exception(f"Database error: {e}")
    except ValueError as e:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating booking {booking_code}: {e}")
        raise


def cancel_booking(booking_code):
    try:
        booking = db.query(Booking).get(booking_code)
        if not booking:
            return False

        if booking.status == BookingStatus.CANCELLED:
            return True  # Вже скасоване

        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow()

        db.commit()
        return True

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error cancelling booking {booking_code}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling booking {booking_code}: {e}")
        raise


def search_bookings(user_id=None, room_id=None, status=None,
                    check_in_from=None, check_in_to=None,
                    check_out_from=None, check_out_to=None):
    """Пошук бронювань за критеріями"""
    try:
        query = db.query(Booking)

        if user_id is not None:
            query = query.filter(Booking.user_id == user_id)

        if room_id is not None:
            query = query.filter(Booking.room_id == room_id)

        if status is not None:
            query = query.filter(Booking.status == status)

        if check_in_from:
            query = query.filter(Booking.check_in_date >= check_in_from)

        if check_in_to:
            query = query.filter(Booking.check_in_date <= check_in_to)

        if check_out_from:
            query = query.filter(Booking.check_out_date >= check_out_from)

        if check_out_to:
            query = query.filter(Booking.check_out_date <= check_out_to)

        bookings = query.order_by(Booking.created_at.desc()).all()
        return bookings

    except SQLAlchemyError as e:
        logger.error(f"Database error searching bookings: {e}")
        raise Exception(f"Database error: {e}")


def get_upcoming_checkins(days=7):
    """Отримати майбутні заїзди"""
    try:
        today = date.today()
        end_date = today + timedelta(days=days)

        bookings = db.query(Booking).filter(
            Booking.status == BookingStatus.ACTIVE,
            Booking.check_in_date >= today,
            Booking.check_in_date <= end_date
        ).order_by(Booking.check_in_date).all()

        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching upcoming checkins: {e}")
        raise Exception(f"Database error: {e}")