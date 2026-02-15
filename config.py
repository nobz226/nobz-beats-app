import os
import os

class Config:
    """Minimal configuration for audio tools."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')

    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    CONVERTED_FOLDER = 'static/converted'

    # Maximum upload size in bytes (default 100 MiB)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))

    # How long to keep converted/derived files before cleanup (seconds)
    FILE_EXPIRY_SECONDS = int(os.getenv('FILE_EXPIRY_SECONDS', 15 * 60))

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
