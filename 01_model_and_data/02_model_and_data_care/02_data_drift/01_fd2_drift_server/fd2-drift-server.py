# On WIN11
#   conda activate fd2_drift_server_no_docker
#   Browse to : http://localhost:5000/report

# In this version, save the report directly in the SQLite database to get persistency but...
# It does'nt work on Heroku (works like a charm on WIN11 host)
# Again : on Heroku there is no way to save locally
# We can :
#   1. Save on AWS S3
#   2. Use PostgreSQL <-- This is what we do here  


# Add a Postgresql to the fd2_drift_server on Heroku
# Add a Config Var named DRIFT_SERVER_SQL_URI with postgresql://u76st...
# In secrets.ps1 add a line $env:DRIFT_SERVER_SQL_URI = "postgresql://u76st...

#```powershell
#conda install psycopg2-binary sqlalchemy -c conda-forge -y
#conda install sqlalchemy -c conda-forge -y
#```

# In requirements.txt, add  
# psycopg2-binary
# sqlalchemy
# pip list --format=freeze > requirements.txt
# Add gunicorn==23.0.0 at the very end

# delete reports.db

# Comment the # import sqlite3

# Push du projet fraud_detection_2 sur GitHub
# DEPUIS LA RACINE du projet fraud_detection_2 (CTRL+SHIFT+ù) : git subtree push --prefix 01_model_and_data/02_model_and_data_care/02_data_drift/01_fd2_drift_server heroku main

# J'ai pas de serveur PostgreSQL en local
# Faut pousser direct sur Heroku
# Faire la difference en DEBUG et PRODUCTION

# DEBUG 
# config:set FLASK_DEBUG=True (heroku ps:restart si besoin)
# Voir create_app() et app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"
# Procfile
# web: python -m flask --app fd2-drift-server run --host=0.0.0.0 --port=$PORT
# Comprendre qu'on va passer par le main ce qui permet à Flask d'utiliser son propre serveur intégré

# PRODUCTION
# config:set FLASK_DEBUG=False
# Voir create_app() et app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"
# Procfile
# web: gunicorn --workers=3 'fd2-drift-server:create_app()'
# # Comprendre qu'on va utiliser nginx, plus passer par main mais par create_app()
# 
# Remplacer app.run(debug=True) par app.run() dans main()
# Ajouter app.config["DEBUG"] = True dans create_app()
# Faudra l'enlever en mode "production" 
#   
# ----------------------------------------------------------------------
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
# k_DB_Path = "./reports.db"
k_Reports_Dir = "./reports"

k_table_name = "reports"

# SQLite
# k_SQL_Create_Table = f"""
# CREATE TABLE {k_table_name} (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     report_name TEXT NOT NULL,
#     created_at TIMESTAMP NOT NULL,
#     report_content TEXT
# );"""

# PostgreSQL
k_SQL_Create_Table = f"""
CREATE TABLE {k_table_name} (
    id SERIAL PRIMARY KEY,
    report_name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    report_content TEXT
);"""



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




# ----------------------------------------------------------------------
def extract_created_at_from_filename(filename: str) -> datetime:
    g_logger.info(f"{inspect.stack()[0][3]}()")

    match = re.search(r"_(\d{8}_\d{6})\.html$", filename)
    if not match:
        raise ValueError(f"Filename '{filename}' does not match the expected format.")

    timestamp_str = match.group(1)  # Extract the YYYYMMJJ_HHMMSS part
    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")


# ----------------------------------------------------------------------
# def update_database(engine: Engine, report_folder: str = k_Reports_Dir) -> None:

def update_database(engine, report_folder: str = k_Reports_Dir) -> None:
    
    g_logger.info(f"{inspect.stack()[0][3]}()")

    report_files = os.listdir(report_folder)

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT report_name FROM reports")
        )
        existing_reports = set(row["report_name"] for row in result)

        for report in report_files:
            if report not in existing_reports:
                # Extract created_at from the filename
                try:
                    created_at = extract_created_at_from_filename(report)
                except ValueError as e:
                    g_logger.warning(f"Skipping file '{report}': {e}")
                    continue # this report is skipped

                # Read the report content
                report_path = os.path.join(report_folder, report)
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Insert the report into the database
                conn.execute(
                    text("""
                        INSERT INTO reports (report_name, created_at, report_content)
                        VALUES (:report_name, :created_at, :report_content)
                    """),
                    {"report_name": report, "created_at": created_at, "report_content": content},
                )
                g_logger.info(f"Added report to database: {report}")
                # os.remove(report_path)
                # g_logger.info(f"{report_path} is removed")

# -----------------------------------------------------------------------------
def check_table_exist(engine, table_name: str) -> bool:

    g_logger.info(f"{inspect.stack()[0][3]}() - Checking table '{table_name}' existence")
    inspector = sqlalchemy_inspect(engine)
    exists = inspector.has_table(table_name)
    g_logger.info(f"Table '{table_name}' exists: {exists}")
    return exists

# -----------------------------------------------------------------------------
def create_table(engine) -> None:
    
    g_logger.info(f"{inspect.stack()[0][3]}() - Creating table '{k_table_name}'")
    try:
        with engine.connect() as conn:
            # TODO : à virer
            conn.execute(text(f"DROP TABLE IF EXISTS {k_table_name}"))
            conn.execute(text(k_SQL_Create_Table))
            g_logger.info(f"Table '{k_table_name}' created successfully.")
            conn.commit()
    except SQLAlchemyError as error:
        g_logger.error(f"Error creating table '{k_table_name}': {error}")


# ----------------------------------------------------------------------
# PostgreSQL database setup
def init_db() -> Engine:
 
    g_logger.info(f"{inspect.stack()[0][3]}()")

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
# double check the content of Procfile file
def create_app() -> Flask:

    g_logger.info(f"{inspect.stack()[0][3]}()")

    app = Flask(__name__)
    # Sur Heroku ou avec Gunicorn. Utilise app.config["DEBUG"] = True car app.run() n’est pas directement invoqué. Gunicorn contrôle le démarrage de l’application.
    # En local avec Flask uniquement : app.run(debug=True) est suffisant pour activer le mode debug pendant les tests. Mais bon ici le code fonctionne en local ET sur Heroku
    # FLASK_DEBUG à definir sur Heroku ou avec heroku config:set FLASK_DEBUG=True
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.logger.info(f"DEBUG mode is {'ON' if app.config['DEBUG'] else 'OFF'}")

    app.logger.info(f"{inspect.stack()[0][3]}()")
    # If you run the app locally you must run ./secrets.ps1 first (see above)
    # In production on Heroku DRIFT_SERVER_SECRET_KEY must have been set manually (see readme.md)
    # Without session key, Flask does not allow the app to set or access the session dictionary
    app.secret_key = os.environ.get("DRIFT_SERVER_SECRET_KEY")

    with app.app_context():
        engine = init_db()  # Initialise la base de données quand l'application est créée

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

        with engine.connect() as conn:
            # Récupérer tous les rapports
            result = conn.execute(
                text("SELECT id, report_name, created_at FROM reports")
            )
            rows = result.fetchall()

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
    # Route pour afficher les rapports d'une date spécifique
    @app.route("/reports")
    def reports_by_date():
        g_logger.info(f"{inspect.stack()[0][3]}()")
        date = request.args.get("date")

        with engine.connect() as conn:
            # Rechercher les rapports du jour sélectionné
            result = conn.execute(
                text("""
                    SELECT id, report_name, created_at
                    FROM reports
                    WHERE DATE(created_at) = :selected_date
                """),
                {"selected_date": date},
            )
            rows = result.fetchall()

        return render_template("reports.html", reports=rows, date=date)

    # ----------------------------------------------------------------------
    # Route pour afficher un rapport spécifique
    @app.route("/report/<int:report_id>")
    def show_report(report_id):
        g_logger.info(f"{inspect.stack()[0][3]}()")

        with engine.connect() as conn:
            # Retrieve the report content from the database
            result = conn.execute(
                text("""
                    SELECT report_name, report_content
                    FROM reports
                    WHERE id = :report_id
                """),
                {"report_id": report_id},
            ).fetchone()

        if result is None:
            abort(404, description="Report not found")

        report_name, report_content = result["report_name"], result["report_content"]

        # Serve the HTML content directly
        return report_content, 200, {"Content-Type": "text/html"}


    # ----------------------------------------------------------------------
    # Route pour sauver le rapport reçu dans la base
    # On ne sauvegarde plus rien dans ./reports
    @app.route("/upload", methods=["POST"])
    def upload_file():
        g_logger.info(f"{inspect.stack()[0][3]}()")

        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Read the content of the uploaded file directly
        content = file.read().decode("utf-8")  # Decode bytes to string

        # Save the report to the database
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO reports (report_name, created_at, report_content)
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
        # db_path = Path(k_DB_Path)
        # if db_path.exists():
        #     db_path.unlink()
        pass

    app = create_app()
    g_logger.info("main()")
    # app.run(debug=True) inutile voir create_app() et app.config["DEBUG"] = ...
    app.run()

    