# routes.py

from flask import jsonify, render_template, request, abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db import get_session
import logging

g_logger = logging.getLogger("fraud_detection_2_drift_server")

def register_routes(app):
    """
    Registers all routes to the Flask app.

    Parameters:
    - app (Flask): Flask application instance.
    """
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/get_reports")
    def get_reports():
        session = get_session()
        try:
            # Query the database using the session
            result = session.execute(
                text("SELECT id, report_name, created_at FROM reports")
            ).mappings()
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

    @app.route("/report/<int:report_id>")
    def show_report(report_id):
        session = get_session()
        try:
            # Retrieve report content
            result = session.execute(
                text(
                    "SELECT report_name, report_content FROM reports WHERE id = :report_id"
                ),
                {"report_id": report_id},
            ).mappings().fetchone()

            if not result:
                abort(404, description="Report not found")

            return result["report_content"], 200, {"Content-Type": "text/html"}
        except SQLAlchemyError:
            raise
        except Exception as e:
            g_logger.error(f"Error in show_report route: {e}")
            raise


    @app.route("/reports")
    def reports_by_date():

        # Get the date parameter from the query string
        date = request.args.get("date")
        if not date:
            return abort(400, "Date parameter is required")

        session = get_session()
        try:
            # Query to fetch reports for the given date
            result = session.execute(
                text("""
                    SELECT id, report_name, created_at
                    FROM reports
                    WHERE DATE(created_at) = :selected_date
                """),
                {"selected_date": date},
            ).mappings()
            rows = [row for row in result]

        except SQLAlchemyError as e:
            g_logger.error(f"Database error while fetching reports for date {date}: {e}")
            return abort(500, "Internal server error")

        # Render the template with the reports
        return render_template("reports.html", reports=rows, date=date)