# logger.py

import logging
import sys
from flask import Flask

g_logger = logging.getLogger("fraud_detection_2_drift_server")
g_logger.setLevel(logging.WARNING)  # Default minimal level to suppress logs


def set_up_logger(app: Flask, debug_level: bool = True) -> None:
    """
    Configures the global logger with console output.

    Parameters:
    - app (Flask): Flask application instance.
    - debug_level (bool): Whether to enable debug-level logging.
    """
    global g_logger

    # Stream handler for console logs
    stream_handler = logging.StreamHandler(sys.stdout)
    log_level = logging.DEBUG if debug_level else logging.INFO
    stream_handler.setLevel(log_level)

    # Format log output
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    stream_handler.setFormatter(formatter)

    # Prevent multiple handlers in case of reinitialization
    if not any(isinstance(h, logging.StreamHandler) for h in g_logger.handlers):
        g_logger.addHandler(stream_handler)

    # Set global logger level
    g_logger.setLevel(log_level)

    # Use Gunicorn logger if available (Heroku production)
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(g_logger.level)

    g_logger.info("=== NEW SESSION START ===")
    g_logger.info(f"DEBUG mode is {'ON' if debug_level else 'OFF'}")
