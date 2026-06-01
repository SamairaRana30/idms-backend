import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET     = os.getenv('JWT_SECRET')
    SUPABASE_URL   = os.getenv('SUPABASE_URL')
    SUPABASE_KEY   = os.getenv('SUPABASE_KEY')
    ENV = os.getenv('ENV', 'development')
    ALLOWED_ORIGINS = os.getenv(
        'ALLOWED_ORIGINS',
        'http://localhost:5000,http://127.0.0.1:5000'
    ).split(',')

    DEV_DATABASE_URL      = os.getenv('DEV_DATABASE_URL')
    STAGING_DATABASE_URL  = os.getenv('STAGING_DATABASE_URL')
    PROD_DATABASE_URL     = os.getenv('PROD_DATABASE_URL')

    _SCHEMA_MAP = {
        'production': 'idms_prod',
        'staging':    'idms_staging',
        'development':'idms_dev',
    }

    @classmethod
    def get_database_url(cls):
        if cls.ENV == 'production':
            return cls.PROD_DATABASE_URL
        if cls.ENV == 'staging':
            return cls.STAGING_DATABASE_URL
        return cls.DEV_DATABASE_URL

    @classmethod
    def get_schema(cls):
        return cls._SCHEMA_MAP.get(cls.ENV, 'idms_dev')
