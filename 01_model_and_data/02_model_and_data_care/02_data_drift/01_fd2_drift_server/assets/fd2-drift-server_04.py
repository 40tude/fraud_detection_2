# On WIN11
#   conda activate fd2_drift_server_no_docker
#   Browse to : http://localhost:5000/report

# In this version, save the report directly in the SQLite database to get persistency but...
# It does'nt work on Heroku (works like a charm on WIN11 host)
# Again : on Heroku there is no way to save locally
# We can :
#   1. Save on AWS S3
#   2. Use PostgreSQL  



# ----------------------------------------------------------------------
import os
import re
import logging
import sqlite3
import inspect
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, render_template, abort      #, send_from_directory

# ----------------------------------------------------------------------
k_DB_Path = "./reports.db"
k_Reports_Dir = "./reports"
k_table_name = "reports"


# ----------------------------------------------------------------------
# Global logger
# logging.basicConfig(level=logging.INFO)
# # logging.basicConfig(
# #     level=logging.INFO,
# #     format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
# #     datefmt='%Y-%m-%d %H:%M:%S'
# # )
# g_logger = logging.getLogger("fraud_detection_2_drift_server")

# Global logger
g_logger = logging.getLogger("fraud_detection_2_drift_server")
g_logger.setLevel(logging.INFO)

# Create a StreamHandler for Heroku logs
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
stream_handler.setFormatter(formatter)

# Add the handler to your logger
g_logger.addHandler(stream_handler)
g_logger.info("=== NEW SESSION START ===")


# ----------------------------------------------------------------------
# See the report_content field
def create_db() -> None:
    g_logger.info(f"{inspect.stack()[0][3]}()")

    # Initialize or connect to the SQLite database
    with sqlite3.connect(k_DB_Path) as conn:
        cursor = conn.cursor()
        # Create the table with the necessary columns
        cursor.execute(
            """
            CREATE TABLE {k_table_name}  (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_name TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                report_content TEXT
            )
            """
        )
        g_logger.info("Database and 'reports' table created successfully.")
        conn.commit()
    return

# ----------------------------------------------------------------------
def extract_created_at_from_filename(filename: str) -> datetime:
    g_logger.info(f"{inspect.stack()[0][3]}()")
    
    match = re.search(r"_(\d{8}_\d{6})\.html$", filename)
    if not match:
        raise ValueError(f"Filename '{filename}' does not match the expected format.")

    timestamp_str = match.group(1)  # Extract the YYYYMMJJ_HHMMSS part
    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")


# ----------------------------------------------------------------------
def update_database(report_folder: str = k_Reports_Dir) -> None:

    g_logger.info(f"{inspect.stack()[0][3]}()")

    # List all reports in the folder
    report_files = os.listdir(report_folder)

    with sqlite3.connect(k_DB_Path) as conn:
        cursor = conn.cursor()

        # Get already recorded reports from the database
        cursor.execute(f"SELECT report_name FROM {k_table_name}")
        existing_reports = set(row[0] for row in cursor.fetchall())

        for report in report_files:
            if report not in existing_reports:
                # Extract created_at from the filename
                try:
                    created_at = extract_created_at_from_filename(report)
                except ValueError as e:
                    g_logger.warning(f"Skipping file '{report}': {e}")
                    continue # this file is skipped

                # Read the report content
                report_path = os.path.join(report_folder, report)
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    g_logger.info(f"Content of {report}: {content[:100]}...")  # Log only the first 100 chars

                # if not content.strip():
                #     g_logger.warning(f"File {report} is empty or could not be read correctly!")
                #     continue  # Skip this file


                # Insert the report into the database
                # SQLite on passe un tuple
                conn.execute(
                    f"""
                        INSERT INTO {k_table_name} (report_name, created_at, report_content)
                        VALUES (:report_name, :created_at, :report_content)
                    """,
                    (report, created_at, content),
                )
                
                # Compatible PostgreSQL - text vient de SQLAlchemy (qu'il faut installer du coup)
                # conn.execute(
                #     text(f"""
                #         INSERT INTO {k_table_name} (report_name, created_at, report_content)
                #         VALUES (:report_name, :created_at, :report_content)
                #     """),
                #     {"report_name": report, "created_at": created_at, "report_content": content},
                # )
                conn.commit() # Ajout explicite du commit
                g_logger.info(f"Added report to database: {report}")
    return


# ----------------------------------------------------------------------
# SQLite database setup
def init_db() -> None:

    g_logger.info(f"{inspect.stack()[0][3]}()")

    if not os.path.exists(k_DB_Path):
        create_db()

    # Call the function to update the database
    update_database(k_Reports_Dir)


# ----------------------------------------------------------------------
# create_app() function is the entry point which configure the Flask app before it runs
# double check the content of Procfile file
def create_app() -> Flask:

    app = Flask(__name__)
    app.logger.info(f"{inspect.stack()[0][3]}()")
    # If you run the app locally you must run ./secrets.ps1 first (see above)
    # In production on Heroku DRIFT_SERVER_SECRET_KEY must have been set manually (see readme.md)
    # Without session key, Flask does not allow the app to set or access the session dictionary
    app.secret_key = os.environ.get("DRIFT_SERVER_SECRET_KEY")

    with app.app_context():
        init_db()  # Initialise la base de données quand l'application est créée

    # Route must be defined inside create_app() otherwise "app" is not yet defined
    # ----------------------------------------------------------------------
    # Flask routes
    # Route pour afficher la page d'accueil avec le calendrier
    @app.route("/")
    def index():
        g_logger.info(f"{inspect.stack()[0][3]}()")
        return render_template("index.html")

    # ----------------------------------------------------------------------
    # Route pour récupérer les rapports sous forme d'événements JSON
    @app.route("/get_reports")
    def get_reports():
        g_logger.info(f"{inspect.stack()[0][3]}()")

        with sqlite3.connect(k_DB_Path) as conn:
            cursor = conn.cursor()

            # Récupérer tous les rapports
            cursor.execute("SELECT id, report_name, created_at FROM reports")
            rows = cursor.fetchall()

        # Formater les rapports pour FullCalendar
        events = [
            {
                "title": f"Report: {row[1]}",
                "start": row[2],  # Format ISO (YYYY-MM-DDTHH:mm:ss)
                "url": f"/report/{row[0]}",  # Lien vers le détail du rapport
            }
            for row in rows
        ]
        return jsonify(events)

    # ----------------------------------------------------------------------
    # Route pour afficher les rapports d'une date spécifique
    @app.route("/reports")
    def reports_by_date():
        g_logger.info(f"{inspect.stack()[0][3]}()")
        date = request.args.get("date")

        with sqlite3.connect(k_DB_Path) as conn:
            cursor = conn.cursor()
            # Rechercher les rapports du jour sélectionné
            cursor.execute(
                """
                SELECT id, report_name, created_at
                FROM reports
                WHERE DATE(created_at) = ?
            """,
                (date,),
            )
            rows = cursor.fetchall()

        return render_template("reports.html", reports=rows, date=date)


    # ----------------------------------------------------------------------
    # Route pour afficher un rapport spécifique
    @app.route("/report/<int:report_id>")
    def show_report(report_id):
        g_logger.info(f"{inspect.stack()[0][3]}()")

        with sqlite3.connect(k_DB_Path) as conn:
            cursor = conn.cursor()

            # Retrieve the report content from the database
            cursor.execute(
                "SELECT report_name, report_content FROM reports WHERE id = ?",
                (report_id,),
            )
            result = cursor.fetchone()

        if result is None:
            abort(404, description="Report not found")

        report_name, report_content = result

        # Serve the HTML content directly
        return report_content, 200, {"Content-Type": "text/html"}


    # ----------------------------------------------------------------------
    # Route pour sauver le rapport reçu dans ./reports

    @app.route("/upload", methods=["POST"])
    def upload_file():
        g_logger.info(f"{inspect.stack()[0][3]}()")

        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_path = os.path.join(k_Reports_Dir, file.filename)
        file.save(file_path)
        g_logger.info(f"Report saved as : {file_path}")

        # Save the content to the database
        with sqlite3.connect(k_DB_Path) as conn:
            cursor = conn.cursor()

            # Read the HTML content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Insert the report with its content
            cursor.execute(
                """
                INSERT INTO reports (report_name, created_at, report_content)
                VALUES (?, ?, ?)
                """,
                (file.filename, datetime.now(), content),
            )
            g_logger.info(f"Saved report '{file.filename}' to the database.")

            conn.commit()

        return jsonify({"message": f"File saved to {file_path}"}), 200

    return app


# ----------------------------------------------------------------------
if __name__ == "__main__":

    # DONE : it seems that locally, in debug mode the application starts twice...
    # Uncomment the print() below to see what happen
    # print(f"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

    # In debug mode, Flask uses an automatic reloader called Werkzeug.
    # This reloader automatically restarts the application whenever it detects a change in the source code.
    # This way, modifications are taken into account without having to restart the application manually.
    # This reloader creates two processes:
    #   - The first process starts the Flask server, then launches the reloader.
    #   - The reloader then restarts the application in a second process to enable hot reloading of the code.
    # This double startup results in the double display of print(f “XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX”)

    # In debug mode, we want to delete the database the very first time
    # That is, when WERKZEUG_RUN_MAIN is still “”.

    os.chdir(Path(__file__).parent)
    g_logger.info(f"Répertoire courant : {Path.cwd()}")

    if os.environ.get("WERKZEUG_RUN_MAIN") == None:
        # if os.path.exists(k_DB_Path):
        # os.remove(k_DB_Path)
        db_path = Path(k_DB_Path)
        if db_path.exists():
            db_path.unlink()

    app = create_app()
    g_logger.info("main()")
    app.run(debug=True)