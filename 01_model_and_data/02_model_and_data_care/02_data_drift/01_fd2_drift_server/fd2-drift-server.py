from flask import Flask
from config import Config
from db import init_db
from logger import set_up_logger
from routes import register_routes

# Entry point of the application
# Original comments about local and Heroku configurations are retained.

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    """
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

    return app


if __name__ == "__main__":
    # Application start for local development
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
