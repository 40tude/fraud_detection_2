# fd2-drift-server.py

# git subtree push --prefix 01_model_and_data/02_model_and_data_care/02_data_drift/01_fd2_drift_server heroku main
# heroku ps:restart --app fd2-drift-server
# heroku logs --tail

# DEBUG -----------------------------------------------------------------------
# Procfile:
# web: python -m flask --app fd2_drift_server run --host=0.0.0.0 --port=$PORT
# Note: This uses Flask's built-in server through the main module
#
# Enable debugging on Heroku:
# heroku config:set FLASK_DEBUG=True --app fd2-drift-server (restart with heroku ps:restart if needed)
#
# Refer to create_app() and app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"

# PRODUCTION ------------------------------------------------------------------
# Procfile:
# web: gunicorn --workers=3 'fd2_drift_server:create_app()'
# Note: This setup uses nginx, bypasses the main module, and directly calls create_app()
# See create_app() et app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "False") == "True"
#
# Disable debugging on Heroku:
# heroku config:set FLASK_DEBUG=False --app fd2-drift-server
#


# Refactor de fd2-drift-server.py
# Split in 5 differents files


# Passage à dotenv
#   l'installer : conda install python-dotenv -c conda-forge -y
#   l'ajouter à requirements.txt
#   Créer ficheir .env
#   Modif de config.py
#   Virer secrets.ps1
#   Modif de fd2-drift-server.py pour vérifier si .env est bien là

# Passage à ScopedSession
#   ScopedSession garantit que chaque thread a sa propre session.
#   Modif de db.py
#   Modif de fd2-drift-server.py (shutdown_session et app.teardown_appcontext(shutdown_session))
#   Modif routes.py pour utiliser ScopedSession

# Gestion des exceptions
#   Modifier fd2-drift-server.py pour ajouter un gestionnaire global pour les erreurs Flask
#   Voir register_error_handlers(app)
#   Modifier routes.py pour y ajouter une gestion centralisée des exceptions
#   Modifier db.py et ajouter update_database() avec gestion des exceptions pour les fichiers
#   et appeler update_database()

# Ajout de la feuille rapport d'un jour particulier
#   Ajouter la route @app.route("/reports") dans routes.py
#   Modfifier templates/reports.html


# ----------------------------------------------------------------------
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from sqlalchemy.exc import SQLAlchemyError

from src.config import Config
from src.logger import set_up_logger
from src.routes import register_routes
from src.db import init_db, shutdown_session

# ----------------------------------------------------------------------
# For mypy
from flask import Response

# from flask.typing import ResponseReturnValue
# from typing import Callable
# RouteFunction = Callable[..., str]


# ----------------------------------------------------------------------
# Entry point of the application
def create_app() -> Flask:
    """
    Create and configure the Flask application.
    """

    # Ensure .env exists and load variables
    os.chdir(Path(__file__).parent)
    env_path = Path(".env")

    # The app use env variables under Heroku and .env content under Windows 11
    is_heroku = os.getenv("DYNO") is not None  # Heroku sets the DYNO environment variable
    if not is_heroku and not env_path.is_file():
        raise FileNotFoundError(".env file is missing. Create one at the root of the project.")

    # if .env is NOT available, no exception and returns False
    load_dotenv(dotenv_path=env_path)

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize the logger
    set_up_logger(app, app.config["DEBUG"])

    # Initialize the database
    with app.app_context():
        init_db()

    # Register routes
    register_routes(app)

    # Used to free the resources linked to the SQLAlchemy session at the end of each request in the Flask application.
    # Flask provides a mechanism called application context, which manages resources specific to each HTTP request.
    # When a request arrives, Flask creates an application context and a request context. These contexts last for the duration of the request.
    # At the end of the request (whether it succeeds or an error occurs), Flask executes the functions registered with teardown_appcontext to clean up the resources.
    # shutdown_session() is defined in db.py
    app.teardown_appcontext(shutdown_session)

    # Register global error handlers
    register_error_handlers(app)

    return app


# ----------------------------------------------------------------------
# Implements global error handlers for the Flask application.
# These handlers automatically catch certain exceptions raised throughout the application and provide a standardized response to the client.
def register_error_handlers(app: Flask) -> None:
    """
    Registers global error handlers for the Flask application.

    Parameters:
    - app (Flask): The Flask application instance.
    """

    # See SQLAlchemyError in db.py
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error: SQLAlchemyError) -> tuple[Response, int]:
        app.logger.error(f"Database error: {error}")
        return jsonify({"error": "A database error occurred"}), 500

    # See update_database() in db.py
    @app.errorhandler(FileNotFoundError)
    def handle_file_not_found_error(error: FileNotFoundError) -> tuple[Response, int]:
        app.logger.error(f"File not found: {error}")
        return jsonify({"error": "The requested file was not found"}), 404

    @app.errorhandler(Exception)
    def handle_general_exception(error: Exception) -> tuple[Response, int]:
        app.logger.error(f"An unexpected error occurred: {error}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Application start for local development
    app = create_app()
    # app.run(host="0.0.0.0", port=5000)
    app.run()
