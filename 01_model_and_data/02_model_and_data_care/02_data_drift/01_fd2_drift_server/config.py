import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# For Mypy


# Load environment variables from the .env file
load_dotenv()


class Config:
    """
    Configuration for the Flask application.
    Variables are loaded from the .env file using dotenv.
    """

    DEBUG = os.getenv("FLASK_DEBUG", "False").strip().lower() in ("true", "1")
    SECRET_KEY = os.getenv("DRIFT_SERVER_SECRET_KEY", "default_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DRIFT_SERVER_SQL_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Recommended to disable unused feature
