from src.api.db import db
from src.api.models.room_model import Amenity, RoomAmenity
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)


def get_all_amenities():
    try:
        amenities = db.query(Amenity).all()
        return amenities
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching amenities: {e}")
        raise Exception(f"Database error: {e}")


def get_amenity_by_id(amenity_id):
    try:
        amenity = db.query(Amenity).get(amenity_id)
        return amenity
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching amenity {amenity_id}: {e}")
        raise Exception(f"Database error: {e}")


def create_amenity(data):
    try:
        amenity_name = data.get('amenity_name')
        icon_url = data.get('icon_url')

        new_amenity = Amenity(
            amenity_name=amenity_name,
            icon_url=icon_url
        )

        db.add(new_amenity)
        db.commit()
        return new_amenity

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating amenity: {e}")
        raise ValueError("Amenity with this name already exists")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating amenity: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating amenity: {e}")
        raise


def update_amenity(amenity_id, data):
    try:
        amenity = db.query(Amenity).get(amenity_id)
        if not amenity:
            return None

        for key, value in data.items():
            if hasattr(amenity, key) and key != 'amenity_id':
                setattr(amenity, key, value)

        db.commit()
        return amenity

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error updating amenity {amenity_id}: {e}")
        raise ValueError("Amenity with this name already exists")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating amenity {amenity_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating amenity {amenity_id}: {e}")
        raise


def delete_amenity(amenity_id):
    try:
        amenity = db.query(Amenity).get(amenity_id)
        if not amenity:
            return False

        db.query(RoomAmenity).filter_by(amenity_id=amenity_id).delete()
        db.delete(amenity)
        db.commit()
        return True

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting amenity {amenity_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting amenity {amenity_id}: {e}")
        raise