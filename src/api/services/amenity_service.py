from src.api.models.room_model import Amenity
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)


def get_all_amenities(session):
    try:
        amenities = session.query(Amenity).all()
        return amenities
    except SQLAlchemyError as e:
        logger.error(f"Database error getting amenities: {e}")
        raise Exception(f"Database error: {e}")


def get_amenity_by_id(session, amenity_id):
    try:
        amenity = session.query(Amenity).get(amenity_id)
        return amenity
    except SQLAlchemyError as e:
        logger.error(f"Database error getting amenity {amenity_id}: {e}")
        raise Exception(f"Database error: {e}")


def get_amenity_by_name(session, amenity_name):
    try:
        amenity = session.query(Amenity).filter_by(amenity_name=amenity_name).first()
        return amenity
    except SQLAlchemyError as e:
        logger.error(f"Database error getting amenity {amenity_name}: {e}")
        raise Exception(f"Database error: {e}")


def create_amenity(session, data):
    try:
        amenity_name = data.get('amenity_name')

        existing = get_amenity_by_name(session, amenity_name)
        if existing:
            raise ValueError(f"Amenity with name '{amenity_name}' already exists")

        new_amenity = Amenity(
            amenity_name=amenity_name,
            icon_url=data.get('icon_url')
        )

        session.add(new_amenity)
        session.commit()
        logger.info(f"Created amenity: {amenity_name}")
        return new_amenity

    except ValueError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error creating amenity: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating amenity: {e}")
        raise


def update_amenity(session, amenity_id, data):
    try:
        amenity = session.query(Amenity).get(amenity_id)
        if not amenity:
            return None

        if 'amenity_name' in data and data['amenity_name'] != amenity.amenity_name:
            existing = get_amenity_by_name(session, data['amenity_name'])
            if existing and existing.amenity_id != amenity_id:
                raise ValueError(f"Amenity with name '{data['amenity_name']}' already exists")

        for key, value in data.items():
            if hasattr(amenity, key) and key != 'amenity_id':
                setattr(amenity, key, value)

        session.commit()
        logger.info(f"Updated amenity {amenity_id}")
        return amenity

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Integrity error updating amenity {amenity_id}: {e}")
        raise ValueError("Amenity name already exists")
    except ValueError:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error updating amenity {amenity_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating amenity {amenity_id}: {e}")
        raise


def delete_amenity(session, amenity_id):
    try:
        amenity = session.query(Amenity).get(amenity_id)
        if not amenity:
            return False

        session.delete(amenity)
        session.commit()
        logger.info(f"Deleted amenity {amenity_id}")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error deleting amenity {amenity_id}: {e}")
        raise Exception(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting amenity {amenity_id}: {e}")
        raise