import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-4-everyone')

    DATABASE_URL = os.environ.get('DATABASE_URL')

    if not DATABASE_URL:
        DATABASE_URL = 'postgresql://postgres:password123@localhost:5433/hotel_db'

    DEBUG = False
    TESTING = False
    ENV = 'production'


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'


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
    else:
        return DevelopmentConfig