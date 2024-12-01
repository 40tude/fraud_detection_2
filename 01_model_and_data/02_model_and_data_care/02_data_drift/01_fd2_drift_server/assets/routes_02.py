# routes.py

from flask import jsonify, render_template, request, abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from db import get_session

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
        except SQLAlchemyError as e:
            app.logger.error(f"Error fetching reports: {e}")
            return jsonify({"error": "Database error"}), 500

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
        except SQLAlchemyError as e:
            app.logger.error(f"Error fetching report {report_id}: {e}")
            return jsonify({"error": "Database error"}), 500
