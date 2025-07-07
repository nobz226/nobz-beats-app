import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///music.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    CONVERTED_FOLDER = 'static/converted'
    
    # API keys
    TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
    

    
    # Session settings
    SESSION_TIMEOUT = 300  # 5 minutes in seconds
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        # Ensure required directories exist
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
