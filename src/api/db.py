from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from src.api.config import get_config

ConfigClass = get_config()

engine = create_engine(ConfigClass.DATABASE_URL)
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
    if ConfigClass.ENV == 'development':
        Base.metadata.create_all(bind=engine)
    else:
        print("Skipping table creation — not in development mode")