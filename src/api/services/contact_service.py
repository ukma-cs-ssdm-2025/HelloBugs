from src.api.models.contact_model import Contact
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


def get_contact_info(session):
    """Отримати контактну інформацію (завжди повертає один запис)"""
    try:
        contact = session.query(Contact).first()
        if not contact:
            # Створюємо запис за замовчуванням якщо його немає
            contact = Contact(
                hotel_name="Готель Хрещатик",
                address="м. Київ, вул. Хрещатик, 5",
                phone="+380956666666",
                email="info@hotel.com",
                schedule="Цілодобово",
                description="Ласкаво просимо до готелю Хрещатик"
            )
            session.add(contact)
            session.commit()
            session.refresh(contact)
        return contact
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching contact info: {e}")
        raise Exception(f"Database error: {e}")


def update_contact_info(session, data):
    """Оновити контактну інформацію (тільки для адміна)"""
    try:
        contact = session.query(Contact).first()
        if not contact:
            contact = Contact()
            session.add(contact)
        
        # Оновлюємо тільки передані поля
        if 'hotel_name' in data:
            contact.hotel_name = data['hotel_name']
        if 'address' in data:
            contact.address = data['address']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'email' in data:
            contact.email = data['email']
        if 'schedule' in data:
            contact.schedule = data['schedule']
        if 'description' in data:
            contact.description = data['description']
        
        session.commit()
        session.refresh(contact)
        return contact
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error updating contact info: {e}")
        raise Exception(f"Database error: {e}")
