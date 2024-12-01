import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import Config
import logging
import re

g_logger = logging.getLogger("fraud_detection_2_drift_server")

# Create the SQLAlchemy engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

# ScopedSession ensures thread-safe database sessions
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def extract_created_at_from_filename(filename: str) -> datetime:
    """
    Extracts the datetime from the report filename.
    Example: report_20231201_120000.html -> 2023-12-01 12:00:00
    """
    match = re.search(r"_(\d{8}_\d{6})\.html$", filename)
    if not match:
        raise ValueError(f"Filename '{filename}' does not match the expected format.")

    timestamp_str = match.group(1)
    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")


def update_database(report_folder: str = "./reports"):
    """
    Updates the database with reports found in the specified folder.

    Parameters:
    - report_folder (str): The folder containing report files.
    """
    session = get_session()
    try:
        # Get list of files in the report folder
        try:
            report_files = os.listdir(report_folder)
        except FileNotFoundError:
            g_logger.warning(f"Report folder '{report_folder}' does not exist.")
            return

        # Fetch existing reports from the database
        with session.begin():
            # SQLAlchemy's .mappings() method converts each line of the result into a dictionary. 
            # This approach is compatible with an SQLAlchemy session.
            result = session.execute(text("SELECT report_name FROM reports")).mappings()
            existing_reports = {row["report_name"] for row in result}

            for report in report_files:
                if report not in existing_reports:
                    try:
                        # Extract datetime from filename
                        created_at = extract_created_at_from_filename(report)
                    except ValueError as e:
                        g_logger.warning(f"Skipping file '{report}': {e}")
                        continue

                    report_path = os.path.join(report_folder, report)
                    try:
                        # Read the file content
                        with open(report_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except IOError as e:
                        g_logger.error(f"Failed to read file '{report_path}': {e}")
                        continue

                    # Insert the report into the database
                    session.execute(
                        text("""
                            INSERT INTO reports (report_name, created_at, report_content)
                            VALUES (:report_name, :created_at, :report_content)
                        """),
                        {"report_name": report, "created_at": created_at, "report_content": content},
                    )
                    g_logger.info(f"Added report to database: {report}")

                    # Optionally delete the file
                    # try:
                    #     os.remove(report_path)
                    #     g_logger.info(f"Deleted file: {report_path}")
                    # except OSError as e:
                    #     g_logger.error(f"Failed to delete file '{report_path}': {e}")
    except SQLAlchemyError as e:
        g_logger.error(f"Database error during update_database: {e}")
        raise

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

        # Update the database with reports from the folder
        update_database()

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
