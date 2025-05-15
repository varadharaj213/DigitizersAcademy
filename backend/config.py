import os
import secrets

class Config:
    """Base configuration class with settings common to all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    # Database configuration
    DB_HOST = os.environ.get('localhost')
    DB_USER = os.environ.get('root')
    DB_PASSWORD = os.environ.get('')
    DB_NAME = os.environ.get('course_registration')
    
    # Email configuration
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 587)
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME') or 'varadharaj160@gmail.com'
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or 'jlsbkoanclltyfdy'
    
    # OTP settings
    OTP_EXPIRY_MINUTES = 10
    
class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True

class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False

# Configuration dictionary to select environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Active configuration (defaults to development)
app_config = config[os.environ.get('FLASK_ENV') or 'default']