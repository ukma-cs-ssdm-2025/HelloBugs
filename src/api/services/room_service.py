from src.api.models.room_model import Room, Amenity, RoomAmenity, RoomType, RoomStatus
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)


def get_all_rooms(session):
    try:
        rooms = session.query(Room).all()
        return rooms
    except Exception as e:
        print(f"{e}")
        return []


def get_room_by_id(session, room_id):
    try:
        room = session.query(Room).get(room_id)
        return room
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching room {room_id}: {e}")
        raise Exception(f"Database error: {e}")


def get_room_by_number(session, room_number):
    try:
        room = session.query(Room).filter_by(room_number=room_number).first()
        return room
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching room {room_number}: {e}")
        raise Exception(f"Database error: {e}")


def create_room(session, data):
    try:
        room_number = data.get('room_number')

        existing_room = get_room_by_number(session, room_number)
        if existing_room:
            print(f"Room {room_number} already exists")
            raise ValueError(f"Room with number {room_number} already exists")

        room_type_str = data.get('room_type')

        try:
            room_type = RoomType[room_type_str]
        except KeyError:
            raise ValueError(
                f"Invalid room_type: {room_type_str}. Must be one of: {', '.join([t.name for t in RoomType])}")

        status_str = data.get('status', 'AVAILABLE')
        try:
            status = RoomStatus[status_str]
        except KeyError:
            raise ValueError(f"Invalid status: {status_str}. Must be one of: {', '.join([s.name for s in RoomStatus])}")

        new_room = Room(
            room_number=room_number,
            room_type=room_type,
            max_guest=data.get('max_guest'),
            base_price=float(data.get('base_price')),
            status=status,
            description=data.get('description'),
            floor=data.get('floor'),
            size_sqm=data.get('size_sqm'),
            main_photo_url=data.get('main_photo_url'),
            photo_urls=data.get('photo_urls', [])
        )
        session.add(new_room)
        session.commit()
        return new_room

    except ValueError as e:
        print(f"ValueError in create_room: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        print(f"ERROR in create_room: {str(e)}")
        print(f"ERROR type: {type(e)}")
        session.rollback()
        raise


def update_room_partial(session, room_id, data):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            return None

        if 'room_type' in data and isinstance(data['room_type'], str):
            try:
                data['room_type'] = RoomType[data['room_type']]
            except KeyError:
                raise ValueError(f"Invalid room_type: {data['room_type']}")

        if 'status' in data and isinstance(data['status'], str):
            try:
                data['status'] = RoomStatus[data['status']]
            except KeyError:
                raise ValueError(f"Invalid status: {data['status']}")

        for key, value in data.items():
            if key == 'amenities':
                continue
            elif hasattr(room, key) and key != 'room_id':
                setattr(room, key, value)

        if 'amenities' in data:
            session.query(RoomAmenity).filter_by(room_id=room_id).delete()
            for amenity_id in data['amenities']:
                amenity = session.query(Amenity).get(amenity_id)
                if amenity:
                    room_amenity = RoomAmenity(
                        room_id=room_id,
                        amenity_id=amenity_id,
                        quantity=1,
                        is_available=True
                    )
                    session.add(room_amenity)

        session.commit()
        return room

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error updating room {room_id}: {e}")
        raise ValueError("Room number already exists")
    except ValueError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error updating room {room_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating room {room_id}: {e}")
        raise


def update_room_full(session, room_id, data):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            return None

        room_type = data.get('room_type')
        if room_type and isinstance(room_type, str):
            try:
                room_type = RoomType[room_type]
            except KeyError:
                raise ValueError(f"Invalid room_type: {room_type}")

        status = data.get('status', 'AVAILABLE')
        if status and isinstance(status, str):
            try:
                status = RoomStatus[status]
            except KeyError:
                raise ValueError(f"Invalid status: {status}")

        room.room_number = data.get('room_number')
        room.room_type = room_type
        room.max_guest = data.get('max_guest')
        room.base_price = float(data.get('base_price'))
        room.status = status
        room.description = data.get('description')
        room.floor = data.get('floor')
        room.size_sqm = data.get('size_sqm')
        room.main_photo_url = data.get('main_photo_url')
        room.photo_urls = data.get('photo_urls', [])

        session.query(RoomAmenity).filter_by(room_id=room_id).delete()
        amenities = data.get('amenities', [])
        for amenity_id in amenities:
            amenity = session.query(Amenity).get(amenity_id)
            if amenity:
                room_amenity = RoomAmenity(
                    room_id=room_id,
                    amenity_id=amenity_id,
                    quantity=1,
                    is_available=True
                )
                session.add(room_amenity)

        session.commit()
        return room

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error updating room {room_id}: {e}")
        raise ValueError("Room number already exists")
    except ValueError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error updating room {room_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating room {room_id}: {e}")
        raise


def delete_room(session, room_id):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            return False

        session.query(RoomAmenity).filter_by(room_id=room_id).delete()
        session.delete(room)
        session.commit()
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error deleting room {room_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting room {room_id}: {e}")
        raise


def search_available_rooms(session, check_in=None, check_out=None, room_type=None,
                           min_price=None, max_price=None, guests=None):
    try:
        query = session.query(Room).filter(Room.status == RoomStatus.AVAILABLE)

        if room_type:
            if isinstance(room_type, str):
                room_type = RoomType[room_type]
            query = query.filter(Room.room_type == room_type)

        if min_price is not None:
            query = query.filter(Room.base_price >= min_price)

        if max_price is not None:
            query = query.filter(Room.base_price <= max_price)

        if guests:
            query = query.filter(Room.max_guest >= guests)

        rooms = query.all()
        return rooms

    except SQLAlchemyError as e:
        logger.error(f"Database error searching rooms: {e}")
        raise Exception(f"Database error: {e}")


def get_room_with_amenities(session, room_id):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            return None
        return room
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching room with amenities {room_id}: {e}")
        raise Exception(f"Database error: {e}")


def get_rooms_by_type(session, room_type):
    try:
        if isinstance(room_type, str):
            room_type = RoomType[room_type]
        rooms = session.query(Room).filter_by(room_type=room_type).all()
        return rooms
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching rooms by type {room_type}: {e}")
        raise Exception(f"Database error: {e}")