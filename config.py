import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# Centralized configuration access re-exported from app.config
from app.config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config_by_name
)

__all__ = [
    'basedir',
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig',
    'config_by_name'
]
