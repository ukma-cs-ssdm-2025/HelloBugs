import os
import sys
from src.api.db import Base, engine
from sqlalchemy import inspect

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def init_database():
    """
    Ініціалізація бази даних - створення таблиць через SQLAlchemy
    """
    try:
        print("Starting database initialization...")

        print("Importing models...")
        from src.api.models.user_model import User
        from src.api.models.room_model import Room, Amenity, RoomAmenity
        from src.api.models.booking_model import Booking
        print("Models imported successfully")

        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("Created tables:")
        for table in tables:
            print(f"   - {table}")

        print(f"Database initialized! Total tables: {len(tables)}")

    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    init_database()