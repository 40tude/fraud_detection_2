# routes.py

from flask import Flask, jsonify, render_template, request, abort, jsonify, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db import get_session
import logging
from datetime import datetime


# -----------------------------------------------------------------------------
# For Mypy
from flask.typing import ResponseReturnValue
from typing import Callable

RouteFunction = Callable[..., str]

g_logger = logging.getLogger("fraud_detection_2_drift_server")


# -----------------------------------------------------------------------------
def register_routes(app: Flask) -> None:
    """
    Registers all routes to the Flask app.

    Parameters:
    - app (Flask): Flask application instance.
    """

    # -------------------------------------------------------------------------
    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    # -------------------------------------------------------------------------
    @app.route("/get_reports")
    def get_reports() -> Response:
        session = get_session()
        try:
            # Query the database using the session
            result = session.execute(text("SELECT id, report_name, created_at FROM reports")).mappings()
            rows = [row for row in result]

            # Format for FullCalendar
            events = [
                {
                    "title": f"Report: {row['report_name']}",
                    "start": row["created_at"].isoformat(),
                    "url": f"/report/{row['id']}",
                }
                for row in rows
            ]
            return jsonify(events)
        except SQLAlchemyError:
            # Let the global SQLAlchemy error handler take over
            raise
        except Exception as e:
            g_logger.error(f"Error in get_reports route: {e}")
            raise  # Let the global error handler take over

    # -------------------------------------------------------------------------
    @app.route("/report/<int:report_id>")
    def show_report(report_id: int) -> tuple[str, int, dict[str, str]]:
        session = get_session()
        try:
            # Retrieve report content
            result = (
                session.execute(
                    text("SELECT report_name, report_content FROM reports WHERE id = :report_id"),
                    {"report_id": report_id},
                )
                .mappings()
                .fetchone()
            )

            if not result:
                abort(404, description="Report not found")

            return result["report_content"], 200, {"Content-Type": "text/html"}
        except SQLAlchemyError:
            raise
        except Exception as e:
            g_logger.error(f"Error in show_report route: {e}")
            raise

    # -------------------------------------------------------------------------
    @app.route("/reports")
    def reports_by_date() -> str:

        # Get the date parameter from the query string
        date = request.args.get("date")
        if not date:
            return abort(400, "Date parameter is required")

        session = get_session()
        try:
            # Query to fetch reports for the given date
            result = session.execute(
                text(
                    """
                    SELECT id, report_name, created_at
                    FROM reports
                    WHERE DATE(created_at) = :selected_date
                """
                ),
                {"selected_date": date},
            ).mappings()
            rows = [row for row in result]

        except SQLAlchemyError as e:
            g_logger.error(f"Database error while fetching reports for date {date}: {e}")
            return abort(500, "Internal server error")

        # Render the template with the reports
        return render_template("reports.html", reports=rows, date=date)

    # -------------------------------------------------------------------------
    @app.route("/upload", methods=["POST"])
    # def upload_file() -> Tuple[Response, int]:
    def upload_file() -> ResponseReturnValue:
        g_logger.debug("Entering /upload")

        # Check if the request contains a file part
        if "file" not in request.files:
            g_logger.warning("No file part in the request")
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]

        # Check if a file is selected
        if not file.filename:
            g_logger.warning("No file selected in the request")
            return jsonify({"error": "No selected file"}), 400

        try:
            # Read the content of the uploaded file
            content = file.read().decode("utf-8")  # Decode bytes to string

            # Save the report into the database
            session = get_session()
            with session.begin():
                session.execute(
                    text(
                        """
                        INSERT INTO reports (report_name, created_at, report_content)
                        VALUES (:report_name, :created_at, :report_content)
                    """
                    ),
                    {
                        "report_name": file.filename,
                        "created_at": datetime.now(),
                        "report_content": content,
                    },
                )
                g_logger.info(f"Saved report '{file.filename}' to the database.")

        except UnicodeDecodeError as e:
            g_logger.error(f"Failed to decode file '{file.filename}': {e}")
            return jsonify({"error": "Failed to decode the file content"}), 400

        except SQLAlchemyError as e:
            g_logger.error(f"Database error while saving report '{file.filename}': {e}")
            return jsonify({"error": "Database error occurred"}), 500

        except Exception as e:
            g_logger.error(f"Unexpected error while uploading file '{file.filename}': {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500

        return jsonify({"message": f"Report '{file.filename}' saved to database."}), 200
