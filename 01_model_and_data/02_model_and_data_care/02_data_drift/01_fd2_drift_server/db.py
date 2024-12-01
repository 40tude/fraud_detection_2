from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import Config
import logging

g_logger = logging.getLogger("fraud_detection_2_drift_server")

# Create the SQLAlchemy engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

# ScopedSession ensures thread-safe database sessions
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """
    Initializes the database by checking or creating the necessary tables.
    """
    try:
        # Check table existence
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name='reports'")
            ).fetchone()
            if not result:
                create_table()
                g_logger.info("Reports table created successfully.")
    except SQLAlchemyError as e:
        g_logger.error(f"Error initializing database: {e}")
        raise


def create_table():
    """
    Creates the `reports` table in the database.
    """
    create_table_query = """
    CREATE TABLE reports (
        id SERIAL PRIMARY KEY,
        report_name TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        report_content TEXT
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_query))
            g_logger.info("Reports table created successfully.")
    except SQLAlchemyError as e:
        g_logger.error(f"Error creating table: {e}")
        raise


def get_session():
    """
    Provides the current scoped session.
    Use this function to get a database session in your routes or logic.
    """
    return db_session


def shutdown_session(exception=None):
    """
    Removes the session at the end of the request to avoid leaks.
    This should be registered with Flask's teardown_appcontext.
    """
    db_session.remove()
