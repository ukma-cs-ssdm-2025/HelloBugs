from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = 'postgresql://postgres:password123@db_local:5433/hotel_db'

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
db = scoped_session(SessionLocal)


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def create_tables():
    Base.metadata.create_all(bind=engine)