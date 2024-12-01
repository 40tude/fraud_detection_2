# routes.py

from flask import jsonify, render_template, request, abort
from sqlalchemy import text
from db import init_db

def register_routes(app):
    """
    Registers all routes to the Flask app.

    Parameters:
    - app (Flask): Flask application instance.
    """
    engine = init_db()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/get_reports")
    def get_reports():
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, report_name, created_at FROM reports")
            ).mappings()
            rows = [row for row in result]

        events = [
            {
                "title": f"Report: {row['report_name']}",
                "start": row["created_at"].isoformat(),
                "url": f"/report/{row['id']}",
            }
            for row in rows
        ]
        return jsonify(events)

    @app.route("/report/<int:report_id>")
    def show_report(report_id):
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT report_name, report_content FROM reports WHERE id = :report_id"
                ),
                {"report_id": report_id},
            ).mappings().fetchone()

        if not result:
            abort(404, description="Report not found")

        return result["report_content"], 200, {"Content-Type": "text/html"}
