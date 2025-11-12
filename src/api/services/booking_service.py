from src.api.models.booking_model import Booking, BookingStatus
from src.api.models.room_model import Room, RoomStatus
from src.api.models.user_model import User
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_, not_
from datetime import datetime, date, timedelta, timezone
import logging
import time
import secrets

logger = logging.getLogger(__name__)


def generate_booking_code():
    timestamp = int(time.time() * 1000) % 1000000
    random_part = secrets.randbelow(90000) + 10000
    return f"BK{timestamp}{random_part}"


def _validate_dates(check_in, check_out):
    if check_in >= check_out:
        raise ValueError("Check-out date must be after check-in date")
    if check_in < date.today():
        raise ValueError("Check-in date cannot be in the past")


def _resolve_user(session, user_id, email, data):
    if user_id:
        user = session.query(User).get(user_id)
        if not user:
            raise ValueError("User not found")
        return user.user_id
    if email:
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            if existing_user.is_registered:
                raise ValueError("This email is already registered. Please log in to make a booking.")
            return existing_user.user_id
        new_guest = User(
            email=email,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            is_registered=False,
            created_at=datetime.now(timezone.utc)
        )
        session.add(new_guest)
        session.flush()
        return new_guest.user_id
    raise ValueError("Either user_id or email must be provided")

def _get_room_or_error(session, room_id):
    room = session.query(Room).get(room_id)
    if not room:
        raise ValueError("Room not found")
    return room

def check_room_availability(session, room_id, check_in, check_out, exclude_booking_code=None):
    try:
        room = session.query(Room).with_for_update().get(room_id)
        if not room or room.status != RoomStatus.AVAILABLE:
            return False, "Room is not available"

        overlapping_query = session.query(Booking).filter(
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
        return overlapping_bookings == 0, "Room is available" if overlapping_bookings == 0 else "Room is already booked"

    except SQLAlchemyError as e:
        logger.error(f"Database error checking room availability: {e}")
        return False, "Database error"

def calculate_total_price(session, room_id, check_in, check_out):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            return 0

        nights = (check_out - check_in).days
        return float(room.base_price) * nights

    except Exception as e:
        logger.error(f"Error calculating total price: {e}")
        return 0

def get_all_bookings(session):
    try:
        bookings = session.query(Booking).all()
        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching bookings: {e}")
        raise Exception(f"Database error: {e}")

def get_booking_by_code(session, booking_code):
    try:
        booking = session.query(Booking).get(booking_code)
        return booking
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching booking {booking_code}: {e}")
        raise Exception(f"Database error: {e}")

def get_user_bookings(session, user_id):
    try:
        bookings = session.query(Booking).filter_by(user_id=user_id).all()
        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching user bookings {user_id}: {e}")
        raise Exception(f"Database error: {e}")

def create_booking(session, data):
    try:
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        _validate_dates(check_in, check_out)

        room_id = data.get('room_id')
        
        room = session.query(Room).with_for_update().get(room_id)
        if not room:
            raise ValueError("Room not found")
        if room.status != RoomStatus.AVAILABLE:
            raise ValueError("Room is not available")

        overlapping = session.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status == BookingStatus.ACTIVE,
            not_(or_(
                check_out <= Booking.check_in_date,
                check_in >= Booking.check_out_date
            ))
        ).count()
        
        if overlapping > 0:
            raise ValueError("Room is already booked")

        user_id = _resolve_user(session, data.get('user_id'), data.get('email'), data)
        
        if not user_id:
            logger.error(f"User resolution failed. Email: {data.get('email')}, UserID: {data.get('user_id')}")
            raise ValueError("Could not resolve user ID for booking.")

        booking_code = generate_booking_code()

        new_booking = Booking(
            booking_code=booking_code,
            user_id=user_id,
            room_id=room_id,
            check_in_date=check_in,
            check_out_date=check_out,
            special_requests=data.get('special_requests'),
            status=data.get('status', BookingStatus.ACTIVE),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        session.add(new_booking)
        return new_booking

    except IntegrityError as e:
        logger.error(f"Integrity error creating booking: {e}")
        if "email" in str(e).lower():
            raise ValueError("This email is already registered. Please log in or use a different email.")
        elif "booking_code" in str(e).lower():
            raise ValueError("System error - please try again")
        else:
            raise ValueError("Database error - please try again")
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise

def update_booking_partial(session, booking_code, data):
    try:
        booking = session.query(Booking).get(booking_code)
        if not booking:
            return None

        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            allowed_fields = {'status'}
            if set(data.keys()) - allowed_fields:
                raise ValueError("Can only change status for completed/cancelled bookings")

        check_in = data.get('check_in_date', booking.check_in_date)
        check_out = data.get('check_out_date', booking.check_out_date)
        room_id = data.get('room_id', booking.room_id)

        if 'check_in_date' in data or 'check_out_date' in data or 'room_id' in data:
            is_available, message = check_room_availability(
                session, room_id, check_in, check_out, booking_code
            )
            if not is_available:
                raise ValueError(message)

        for key, value in data.items():
            if hasattr(booking, key) and key not in ['booking_code', 'created_at']:
                setattr(booking, key, value)

        booking.updated_at = datetime.now(timezone.utc)
        return booking

    except Exception as e:
        logger.error(f"Error updating booking {booking_code}: {e}")
        raise

def update_booking_full(session, booking_code, data):
    try:
        booking = session.query(Booking).get(booking_code)
        if not booking:
            return None

        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise ValueError("Cannot modify completed or cancelled bookings")

        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        room_id = data.get('room_id')

        is_available, message = check_room_availability(
            session, room_id, check_in, check_out, booking_code
        )
        if not is_available:
            raise ValueError(message)

        booking.user_id = data.get('user_id')
        booking.room_id = data.get('room_id')
        booking.check_in_date = check_in
        booking.check_out_date = check_out
        booking.special_requests = data.get('special_requests')
        booking.updated_at = datetime.now(timezone.utc)

        return booking

    except Exception as e:
        logger.error(f"Error updating booking {booking_code}: {e}")
        raise

def cancel_booking(session, booking_code):
    try:
        booking = session.query(Booking).get(booking_code)
        if not booking:
            return False

        if booking.status == BookingStatus.CANCELLED:
            return True

        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.now(timezone.utc)
        return True

    except Exception as e:
        logger.error(f"Error cancelling booking {booking_code}: {e}")
        raise

def search_bookings(session, user_id=None, room_id=None, status=None,
                    check_in_from=None, check_in_to=None,
                    check_out_from=None, check_out_to=None):
    try:
        query = session.query(Booking)

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

def get_upcoming_checkins(session, days=7):
    try:
        today = date.today()
        end_date = today + timedelta(days=days)

        bookings = session.query(Booking).filter(
            Booking.status == BookingStatus.ACTIVE,
            Booking.check_in_date >= today,
            Booking.check_in_date <= end_date
        ).order_by(Booking.check_in_date).all()

        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching upcoming checkins: {e}")
        raise Exception(f"Database error: {e}")

def get_room_booked_ranges(session, room_id: int, start_date: date, end_date: date):
    """Return list of occupied date ranges for the room within [start_date, end_date].
    Dates are returned as dicts: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    where end is exclusive (check_out_date).
    """
    try:
        from src.api.models.booking_model import Booking, BookingStatus
        overlapping = session.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status != BookingStatus.CANCELLED,
            ~(((Booking.check_out_date <= start_date)) | ((Booking.check_in_date >= end_date)))
        ).all()

        from datetime import datetime as _dt, date as _date

        def _to_date(v):
            if isinstance(v, _date) and not isinstance(v, _dt):
                return v
            if isinstance(v, _dt):
                return v.date()
            try:
                return _date.fromisoformat(str(v)[:10])
            except Exception:
                return v

        s_start = _to_date(start_date)
        s_end = _to_date(end_date)

        ranges = []
        for b in overlapping:
            b_start = _to_date(b.check_in_date)
            b_end = _to_date(b.check_out_date)
            s = max(b_start, s_start)
            e = min(b_end, s_end)
            ranges.append({
                "start": s.isoformat(),
                "end": e.isoformat()
            })
        return ranges
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching booked ranges for room {room_id}: {e}")
        raise Exception(f"Database error: {e}")