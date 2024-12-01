import os


class Config:
    """
    Configuration for the Flask application.
    Handles both local and Heroku environments.
    """
    DEBUG = os.environ.get("FLASK_DEBUG", "False").strip().lower() in ("true", "1")
    SECRET_KEY = os.environ.get("DRIFT_SERVER_SECRET_KEY", "default_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DRIFT_SERVER_SQL_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Recommended to disable unused feature
