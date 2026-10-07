import os
from dotenv import load_dotenv

load_dotenv()

# Explicit absolute paths to project root and app directory
basedir = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(basedir))

# Instance directory resolution (supports app.instance_path or basedir/instance)
INSTANCE_DIR = os.path.join(PROJECT_ROOT, 'instance')
DEFAULT_SQLITE_PATH = os.path.join(INSTANCE_DIR, 'pms.db')

def _resolve_database_uri():
    """Resolve database URI with support for PostgreSQL (Render) and absolute SQLite paths."""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Handle Render PostgreSQL URI dialect requirement
        if db_url.startswith('postgres://'):
            return db_url.replace('postgres://', 'postgresql://', 1)
        # Convert any relative SQLite URI to an explicit absolute path
        if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
            rel_name = db_url.replace('sqlite:///', '', 1)
            if os.path.isabs(rel_name):
                return 'sqlite:///' + rel_name
            if rel_name.startswith('instance/'):
                return 'sqlite:///' + os.path.join(PROJECT_ROOT, rel_name)
            return 'sqlite:///' + os.path.join(INSTANCE_DIR, os.path.basename(rel_name))
        return db_url
    return 'sqlite:///' + DEFAULT_SQLITE_PATH


class Config:
    """Base configuration with explicit absolute paths for production reliability."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pms-default-production-key-change-me')
    
    # Absolute database URI
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads path setup (explicit absolute path)
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'zip', 'docx', 'doc', 'tar.gz', 'pptx'}

    # Flask-Mail / SMTP Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@university.edu')
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    MAIL_SUPPRESS_SEND = True


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
