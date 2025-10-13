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
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        for table in tables:
            print(f" {table}")

        print(f"Database initialized! Total tables: {len(tables)}")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


if __name__ == '__main__':
    init_database()