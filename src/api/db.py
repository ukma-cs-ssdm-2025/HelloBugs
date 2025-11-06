from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv
import os

load_dotenv()  # підхоплює змінні з .env

DATABASE_URL = os.getenv("DATABASE_URL")  # бере актуальний URL
connect_args = {}

if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
else:
    if DATABASE_URL and ("postgres" in DATABASE_URL or "postgresql" in DATABASE_URL or "mysql" in DATABASE_URL):
        connect_args["connect_timeout"] = 5

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,       # every 30 min
        pool_timeout=10,  
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
db = scoped_session(SessionLocal)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)