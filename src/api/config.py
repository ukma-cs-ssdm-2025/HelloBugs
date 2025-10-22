import os
from sqlalchemy import create_engine

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-4-everyone')

    DATABASE_URL = os.environ.get('DATABASE_URL')

    if not DATABASE_URL:
        DATABASE_URL = 'postgresql://postgres:password123@db_local:5433/hotel_db'

    DEBUG = False
    TESTING = False
    ENV = 'production'


class DevelopmentConfig(Config):
    """
    Локальна розробка
    """
    DEBUG = True
    ENV = 'development'


class TestingConfig(Config):
    """
    Винятково для тестування
    """
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    DATABASE_URL = "postgresql://postgres:password123@db_test:5432/hotel_db_test"


    if 'test' not in DATABASE_URL:
        raise RuntimeError(f"Unsafe DATABASE_URL for testing: {DATABASE_URL}")


class StagingConfig(Config):
    DEBUG = True
    ENV = 'staging'


class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'


def get_config():
    env = os.environ.get('RAILWAY_ENVIRONMENT', 'development').lower()

    if env == 'production':
        return ProductionConfig
    elif env == 'staging':
        return StagingConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig

ConfigClass = get_config()
engine = create_engine(ConfigClass.DATABASE_URL)