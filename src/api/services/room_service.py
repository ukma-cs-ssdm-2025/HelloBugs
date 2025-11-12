from src.api.models.room_model import Room, Amenity, RoomAmenity, RoomType, RoomStatus
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)


def get_all_rooms(session):
    try:
        rooms = session.query(Room).all()
        return rooms
    except SQLAlchemyError as e:
        logger.error(f"Database error getting rooms: {e}")
        raise Exception(f"Database error: {e}")


def get_room_by_id(session, room_id):
    try:
        room = session.query(Room).get(room_id)
        return room
    except SQLAlchemyError as e:
        logger.error(f"Database error getting room {room_id}: {e}")
        raise Exception(f"Database error: {e}")


def get_room_by_number(session, room_number):
    try:
        room = session.query(Room).filter_by(room_number=room_number).first()
        return room
    except SQLAlchemyError as e:
        logger.error(f"Database error getting room {room_number}: {e}")
        raise Exception(f"Database error: {e}")


def create_room(session, data):
    try:
        room_number = data.get('room_number')

        existing_room = get_room_by_number(session, room_number)
        if existing_room:
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
            raise ValueError(
                f"Invalid status: {status_str}. Must be one of: {', '.join([s.name for s in RoomStatus])}")

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
        logger.info(f"Created room: {room_number}")
        return new_room

    except ValueError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error creating room: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating room: {e}")
        raise


def update_room_partial(session, room_id, data):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            raise ValueError(f"Room with ID {room_id} not found")

        if 'room_number' in data and data['room_number'] != room.room_number:
            existing = get_room_by_number(session, data['room_number'])
            if existing and existing.room_id != room_id:
                raise ValueError(f"Room with number {data['room_number']} already exists")

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
        logger.info(f"Updated room {room_id}")
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
            raise ValueError(f"Room with ID {room_id} not found")

        if data.get('room_number') != room.room_number:
            existing = get_room_by_number(session, data.get('room_number'))
            if existing and existing.room_id != room_id:
                raise ValueError(f"Room with number {data.get('room_number')} already exists")

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
        logger.info(f"Fully updated room {room_id}")
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
            raise ValueError(f"Room with ID {room_id} not found")

        session.query(RoomAmenity).filter_by(room_id=room_id).delete()
        session.delete(room)
        session.commit()
        logger.info(f"Deleted room {room_id}")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error deleting room {room_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting room {room_id}: {e}")
        raise


def get_room_with_amenities(session, room_id):
    try:
        room = session.query(Room).get(room_id)
        if not room:
            raise ValueError(f"Room with ID {room_id} not found")
        return room
    except SQLAlchemyError as e:
        logger.error(f"Database error getting room with amenities {room_id}: {e}")
        raise Exception(f"Database error: {e}")


def get_rooms_by_type(session, room_type):
    try:
        if isinstance(room_type, str):
            room_type = RoomType[room_type]
        rooms = session.query(Room).filter_by(room_type=room_type).all()
        return rooms
    except SQLAlchemyError as e:
        logger.error(f"Database error getting rooms by type {room_type}: {e}")
        raise Exception(f"Database error: {e}")