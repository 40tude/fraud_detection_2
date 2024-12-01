# db.py

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

g_logger = logging.getLogger("fraud_detection_2_drift_server")

def init_db():
    """
    Initializes the PostgreSQL database by checking or creating necessary tables.
    """
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    try:
        with engine.connect() as conn:
            # Check table existence
            table_check = text("SELECT 1 FROM information_schema.tables WHERE table_name='reports'")
            result = conn.execute(table_check).fetchone()

            if not result:
                create_table(engine)
                g_logger.info("Reports table created successfully.")
    except SQLAlchemyError as e:
        g_logger.error(f"Error initializing database: {e}")
        raise


def create_table(engine):
    """
    Creates the `reports` table in the PostgreSQL database.
    """
    create_table_query = """
    CREATE TABLE reports (
        id SERIAL PRIMARY KEY,
        report_name TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        report_content TEXT
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_table_query))
