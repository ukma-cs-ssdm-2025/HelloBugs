import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-4-everyone')
    DATABASE_URL = os.environ.get('DATABASE_URL')

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    if not DATABASE_URL:
        DATABASE_URL = 'postgresql://postgres:password123@db_local:5433/hotel_db'

    DEBUG = False
    TESTING = False
    ENV = 'production'


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'


class TestingConfig(Config):
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