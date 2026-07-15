import os
from datetime import timedelta

class Config:
    # Flask Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_secret_biblioteca_12345')
    
    # SQLAlchemy Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'biblioteca.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt_dev_secret_biblioteca_54321')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    
    # Business Rules
    MAX_ACTIVE_LOANS = 3
    FINE_PER_DAY = 2.0  # Cost per day of delay
    LOAN_DAYS = 14      # Default loan duration in days
    RESERVATION_HOLD_HOURS = 48  # Time for reservation pick up
