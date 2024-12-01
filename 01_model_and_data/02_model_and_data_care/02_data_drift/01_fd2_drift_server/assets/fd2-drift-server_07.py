# On Windows 11
#   Activate the environment: conda activate fd2_drift_server_no_docker
#   Browse to: http://localhost:5000/report

# In this version, save the report directly in the SQLite database for persistency, but...
# It doesn't work on Heroku (works perfectly on a Windows 11 host)
# Reminder: On Heroku, there is no way to save files locally
# Possible solutions:
#   1. Save on AWS S3
#   2. Use PostgreSQL <-- This is the approach used here

# Add a PostgreSQL database to the fd2_drift_server on Heroku
# Add a Config Var named          DRIFT_SERVER_SQL_URI = postgresql://u76st...
# In secrets.ps1, add the following line: $env:DRIFT_SERVER_SQL_URI = "postgresql://u76st..."

# Install the required dependencies using PowerShell:
# ```powershell
# conda install psycopg2-binary sqlalchemy -c conda-forge -y
# conda install sqlalchemy -c conda-forge -y
# ```

# Update the requirements.txt file by adding:
# psycopg2-binary
# sqlalchemy
# Run: pip list --format=freeze > requirements.txt
# Add gunicorn==23.0.0 at the very end

# Example requirements.txt content:
# blinker==1.9.0
# click==8.1.7
# colorama==0.4.6
# Flask==3.1.0
# importlib_metadata==8.5.0
# itsdangerous==2.2.0
# Jinja2==3.1.4
# MarkupSafe==3.0.2
# pip==24.2
# setuptools==75.1.0
# Werkzeug==3.1.3
# wheel==0.44.0
# zipp==3.21.0
# greenlet==3.1.1
# typing_extensions==4.12.2
# psycopg2-binary==2.9.9
# SQLAlchemy==2.0.36
# gunicorn==23.0.0

# Delete the SQLite database file `reports.db`

# Comment out the line importing sqlite3 (# import sqlite3)

# Push the fraud_detection_2 project to GitHub
# FROM THE ROOT of the fraud_detection_2 project (CTRL+SHIFT+ù): 
# git subtree push --prefix 01_model_and_data/02_model_and_data_care/02_data_drift/01_fd2_drift_server heroku main

# No local PostgreSQL server available
# Push changes directly to Heroku
# Manage differences between DEBUG and PRODUCTION modes

# Replace app.run(debug=True) with app.run() in main()
# Add app.config["DEBUG"] = True in create_app()
# This must be removed in "production" mode

# DEBUG -----------------------------------------------------------------------
# Procfile:
# web: python -m flask --app fd2-drift-server run --host=0.0.0.0 --port=$PORT
# Note: This uses Flask's built-in server through the main module
#
# Enable debugging on Heroku:
# heroku config:set FLASK_DEBUG=True --app fd2-drift-server (restart with heroku ps:restart if needed)
#
# Refer to create_app() and app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"

# PRODUCTION ------------------------------------------------------------------
# Procfile:
# web: gunicorn --workers=3 'fd2-drift-server:create_app()'
# Note: This setup uses nginx, bypasses the main module, and directly calls create_app()
# See create_app() et app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"
#
# Disable debugging on Heroku:
# heroku config:set FLASK_DEBUG=False --app fd2-drift-server
#

# DEPLOY ----------------------------------------------------------------------
# Commit & sync changes in VSCode
# Push changes to Heroku:
# git subtree push --prefix 01_model_and_data/02_model_and_data_care/02_data_drift/01_fd2_drift_server heroku main
# Restart the Heroku app:
# heroku ps:restart --app fd2-drift-server
# View logs:
# heroku logs --tail

# ----------------------------------------------------------------------
# Heroku CLI commands:
# Restart dynos: heroku ps:restart --app fd2-drift-server
#   (Restarts all dynos by default. Use heroku ps:restart web --app <app_name> to restart specific dynos.)
# Restart the entire app: heroku restart --app fd2-drift-server
# Open the app in a browser via CLI: heroku open --app fd2-drift-server


import os
import re
import sys
import logging
import inspect
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, text, inspect as sqlalchemy_inspect, Engine
from flask import Flask, jsonify, request, render_template, abort      #, send_from_directory

# ----------------------------------------------------------------------
k_Reports_Dir = "./reports"
k_table_name = "reports"

# PostgreSQL (does not have AUTOINCREMENT)
k_PostgreSQL_Create_Table = f"""
CREATE TABLE {k_table_name} (
    id SERIAL PRIMARY KEY,
    report_name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    report_content TEXT
);"""



# ----------------------------------------------------------------------
# Global logger - Default minimal configuration
# DEBUG INFO WARNING ERROR CRITICAL
g_logger = logging.getLogger("fraud_detection_2_drift_server")
g_logger.setLevel(logging.WARNING)  # Minimal level to prevent unwanted logs
if not g_logger.hasHandlers():
    g_logger.addHandler(logging.NullHandler())  # Prevent errors before setup



# ----------------------------------------------------------------------
# Global logger
def set_up_logger(app:Flask, debug_level:bool=True)->None:
    
    global g_logger

    # Stream handler for console and Heroku
    stream_handler = logging.StreamHandler(sys.stdout)

    # To have different log levels for local (e.g. DEBUG) and production (INFO) logs
    # Configure log levels dynamically 
    log_level = logging.DEBUG if debug_level else logging.INFO
    stream_handler.setLevel(log_level)
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    stream_handler.setFormatter(formatter)

    # Avoid adding multiple handlers if this function is called again
    if not any(isinstance(h, logging.StreamHandler) for h in g_logger.handlers):
        g_logger.addHandler(stream_handler)

    # Set the global logger level
    g_logger.setLevel(log_level)
    
    # Redirect Flask logs to the global logger (only if Gunicorn is available)
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers  # Use Gunicorn's log handlers on Heroku
        app.logger.setLevel(g_logger.level)  # Align Flask log level with g_logger

    g_logger.info("=== NEW SESSION START ===")
    g_logger.info(f"DEBUG mode is {'ON' if debug_level else 'OFF'}")
    return



# ----------------------------------------------------------------------
def extract_created_at_from_filename(filename: str) -> datetime:
    
    g_logger.debug(f"{inspect.stack()[0][3]}()")

    match = re.search(r"_(\d{8}_\d{6})\.html$", filename)
    if not match:
        g_logger.info(f"{filename} : {filename}' does not match the expected format")
        raise ValueError(f"Filename '{filename}' does not match the expected format.")

    timestamp_str = match.group(1)  # Extract the YYYYMMJJ_HHMMSS part
    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")



# ----------------------------------------------------------------------
# Potentially, several reports are inserted into the database.
# It makes sense to use engine.begin() here, as we want to guarantee that all insertions linked to a call are validated or cancelled together in the event of an error.
def update_database(engine: Engine, report_folder: str = k_Reports_Dir) -> None:
    g_logger.debug(f"{inspect.stack()[0][3]}()")

    report_files = os.listdir(report_folder)

    # With engine.begin(), changes are automatically committed or rolled back
    # With engine.connect(), an explicit commit is required to save changes to the database
    # engine.connect() should be used for read-only operations without modifications, or when transactions are not required.
    # Use this approach for scenarios where you explicitly manage commit() and rollback() 
    # (e.g., in complex logic or in debug mode).

    with engine.begin() as conn:
        result = conn.execute(text(f"SELECT report_name FROM {k_table_name}"))
        existing_reports = set(row["report_name"] for row in result)

        for report in report_files:
            if report not in existing_reports:
                # Extract created_at from the filename
                try:
                    created_at = extract_created_at_from_filename(report)
                except ValueError as e:
                    g_logger.info(f"Skipping file '{report}': {e}")
                    continue

                # Read the report content
                report_path = os.path.join(report_folder, report)
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    g_logger.info(f"Content of {report}: {content[:100]}...")

                # Insert the report into the database
                # PostgreSQL on passe un dictionnaire + text() évite les injections
                conn.execute(
                    text(f"""
                        INSERT INTO {k_table_name} (report_name, created_at, report_content)
                        VALUES (:report_name, :created_at, :report_content)
                    """),
                    {"report_name": report, "created_at": created_at, "report_content": content},
                )
                g_logger.info(f"Added report to database: {report}")
                # os.remove(report_path)
                # g_logger.info(f"{report_path} is removed")
    return



# -----------------------------------------------------------------------------
# This function only checks the existence of a table without modifying the database.
# Keep using engine.connect() since no transaction is required.
def check_table_exist(engine, table_name: str) -> bool:

    g_logger.debug(f"{inspect.stack()[0][3]}() - Checking table '{table_name}' existence")
    inspector = sqlalchemy_inspect(engine)
    exists = inspector.has_table(table_name)
    g_logger.info(f"Table '{table_name}' exists: {exists}")
    return exists



# -----------------------------------------------------------------------------
# A table is being created, a single and critical operation. If it fails, we want to roll back any changes.
# Using engine.begin() is appropriate in this case.
def create_table(engine) -> None:
    g_logger.debug(f"{inspect.stack()[0][3]}() - Creating table '{k_table_name}'")
    try:
        with engine.begin() as conn:
            conn.execute(text(k_PostgreSQL_Create_Table))
            g_logger.info(f"Table '{k_table_name}' re-created successfully.")
    except SQLAlchemyError as error:
        g_logger.error(f"Error creating table '{k_table_name}': {error}")
     


# ----------------------------------------------------------------------
# PostgreSQL database setup
def init_db() -> Engine:
 
    g_logger.debug(f"{inspect.stack()[0][3]}()")

    database_url = os.getenv("DRIFT_SERVER_SQL_URI")
    engine = create_engine(database_url)
    bExist = check_table_exist(engine, k_table_name)
    if not bExist:
        create_table(engine)
        g_logger.info("The table has been created")
        update_database(engine)
        g_logger.info("The table has been updated")
    else:
        g_logger.info("The table already exists")
    return engine



# ----------------------------------------------------------------------
# create_app() function is the entry point which configure the Flask app before it runs
# double check the content of Procfile file AND the FLASK_DEBUG envi variable
def create_app() -> Flask:
    
    app = Flask(__name__)

    # Sur Heroku ou avec Gunicorn. 
    # Utilise app.config["DEBUG"] = True car app.run() n’est pas directement invoqué. 
    # Gunicorn contrôle le démarrage de l’application et il se branche sur create_app() directement
    # En local avec Flask uniquement : app.run(debug=True) dans le main() serait suffisant pour activer le mode debug pendant les tests. 
    # Mais ici le code fonctionne en local ET sur Heroku
    # FLASK_DEBUG est à definir sur Heroku ou avec heroku config:set FLASK_DEBUG=True
    # En local faut utiliser secrets.ps1

    # On Heroku or with Gunicorn :
    #       Use app.config["DEBUG"] = True because app.run() is not directly invoked.
    #       Gunicorn manages the application startup and connects directly to create_app().
    #       FLASK_DEBUG must be defined on Heroku using: heroku config:set FLASK_DEBUG=True
    #
    # Locally with Flask only: 
    #       app.run(debug=True) in the main() would be sufficient to enable debug mode during testing.
    #       However, in this setup, the code works both locally AND on Heroku.
    #       Locally, use secrets.ps1 to set the value of FLASK_DEBUG

    # ! os.environ.get() retournait 1
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False").strip().lower() in ("true", "1")
    set_up_logger(app, app.config["DEBUG"])
    
    g_logger.debug(f"{inspect.stack()[0][3]}()")

    # If you run the app locally you must run ./secrets.ps1 first 
    # In production on Heroku DRIFT_SERVER_SECRET_KEY must have been set manually (see readme.md)
    # Without session key, Flask does not allow the app to set or access the session dictionary
    app.secret_key = os.environ.get("DRIFT_SERVER_SECRET_KEY")

    with app.app_context():
        engine = init_db()  # Initialise la base de données quand l'application est créée

    # ----------------------------------------------------------------------
    # Flask routes
    # Routes must be defined inside create_app() otherwise "app" is not yet defined
    # Route pour afficher la page d'accueil avec le calendrier
    @app.route("/")
    def index():
        g_logger.debug(f"{inspect.stack()[0][3]}()")
        return render_template("index.html")

    # ----------------------------------------------------------------------
    # Route to retrieve reports in the form of JSON events
    @app.route("/get_reports")
    def get_reports():
        g_logger.debug(f"{inspect.stack()[0][3]}()")

        with engine.connect() as conn:
            # Récupérer tous les rapports
            result = conn.execute(
                text(f"SELECT id, report_name, created_at FROM {k_table_name}")
            ).mappings()
            rows = [row for row in result]  # Convert to dicts

        # Formater les rapports pour FullCalendar
        events = [
            {
                "title": f"Report: {row['report_name']}",
                "start": row['created_at'].isoformat(),  # Format ISO (YYYY-MM-DDTHH:mm:ss)
                "url": f"/report/{row['id']}",  # Lien vers le détail du rapport
            }
            for row in rows
        ]
        return jsonify(events)



    # ----------------------------------------------------------------------
    # Route to display reports at a specific date
    @app.route("/reports")
    def reports_by_date():
        g_logger.debug(f"{inspect.stack()[0][3]}()")
        date = request.args.get("date")

        with engine.connect() as conn:
            # Look for the reports of a specific date
            result = conn.execute(
                text(f"""
                    SELECT id, report_name, created_at
                    FROM {k_table_name}
                    WHERE DATE(created_at) = :selected_date
                """),
                {"selected_date": date},
            )
            rows = result.fetchall()

        return render_template("reports.html", reports=rows, date=date)



    # ----------------------------------------------------------------------
    # Route to display one report 
    @app.route("/report/<int:report_id>")
    def show_report(report_id):
        g_logger.debug(f"{inspect.stack()[0][3]}()")

        with engine.connect() as conn:
            # Retrieve the report content from the database
            result = conn.execute(
                text(f"""
                    SELECT report_name, report_content
                    FROM {k_table_name}
                    WHERE id = :report_id
                """),
                {"report_id": report_id},
            ).mappings().fetchone()

        if result is None:
            abort(404, description="Report not found")

        report_name, report_content = result["report_name"], result["report_content"]
        g_logger.info(f"Report {report_name} content length = {len(report_content)}")
        # Serve the HTML content directly
        return report_content, 200, {"Content-Type": "text/html"}



    # ----------------------------------------------------------------------
    # Route to save in the PostgreSQL database the received report 
    # Reports are no longer "saved" in ./reports
    # ./reports only exist because when deploying on Heroku the very first time it help to feed the databased and to show few reports
    @app.route("/upload", methods=["POST"])
    def upload_file():
        g_logger.debug(f"{inspect.stack()[0][3]}()")

        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Read the content of the uploaded file directly
        content = file.read().decode("utf-8")  # Decode bytes to string

        # Save the report into the database
        # engine.begin() => no explicit commit required
        # engine.begin() is used for transactional operations where multiple steps need to be completed together
        # or rolled back in case of an error (e.g., multiple inserts or conditional deletions).
        # Use it to ensure a transaction is properly committed or rolled back, even in case of exceptions.
        with engine.begin() as conn:
            conn.execute(
                text(f"""
                    INSERT INTO {k_table_name} (report_name, created_at, report_content)
                    VALUES (:report_name, :created_at, :report_content)
                """),
                {
                    "report_name": file.filename,
                    "created_at": datetime.now(),
                    "report_content": content,
                }
            )
            g_logger.info(f"Saved report '{file.filename}' to the database.")

        return jsonify({"message": f"Report '{file.filename}' saved to database."}), 200
    return app



# ----------------------------------------------------------------------
if __name__ == "__main__":

    os.chdir(Path(__file__).parent)

    # In debug mode, Flask uses a reloader (Werkzeug) that restarts the application to detect changes in the source code.
    # This restart results in two initializations:
    #   The first process starts Flask and initializes the application.
    #   The reloader starts a new instance of the process to enable hot reloading.
    # Solution to avoid duplicates:
    #   Add a condition to check if the application is started by the reloader or directly by Flask.

    # This should not be confused with the fact that in production mode, we may have 3 working threads, 3 initializations etc. (see logs)
    if os.environ.get("WERKZEUG_RUN_MAIN") == True:
        # This block is executed by the reloader process
        app = create_app()
        g_logger.debug(f"{inspect.stack()[0][3]}()")
        g_logger.debug(f"Répertoire courant : {Path.cwd()}")
        # app.run(debug=True) is useless here see in the create_app() function, the app.config["DEBUG"] = ...
        app.run()


    
    