import os
import os

class Config:
    """Minimal configuration for audio tools."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')

    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    CONVERTED_FOLDER = 'static/converted'

    # Session settings
    SESSION_TIMEOUT = 300  # 5 minutes in seconds

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.CONVERTED_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Use stronger secret key in production
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
