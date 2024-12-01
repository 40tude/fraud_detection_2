# fd2-drift-server.py

# Split de fd2-drift-server.py

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
#   Modifier fd2-drift-server.py


from flask import Flask
from config import Config
from db import init_db, shutdown_session
from logger import set_up_logger
from routes import register_routes
from pathlib import Path
from dotenv import load_dotenv
import os

# Entry point of the application
# Original comments about local and Heroku configurations are retained.

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    """

    # Ensure .env exists and load variables
    os.chdir(Path(__file__).parent)
    env_path = Path(".env")
    # Should be done iff it runs on Windows 11
    # if not env_path.is_file():
        # raise FileNotFoundError(".env file is missing. Create one at the root of the project.")
    # if .env is NOT available, no exception and returns False
    # The app use env variables under Heroku and .env content under Windows 11    
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

    # Remove the database session after each request
    app.teardown_appcontext(shutdown_session)

    return app


if __name__ == "__main__":
    # Application start for local development
    app = create_app()
    # app.run(host="0.0.0.0", port=5000)
    app.run()

