"""
@description
Entry-point script for running the Dash/Flask server with optional HTTPS support.  
It loads environment variables, reads YAML configs, and starts the web application.  
If `SSL_CERT_FILE` and `SSL_KEY_FILE` environment variables are specified, the app
will run under HTTPS using those certificate/key files. Otherwise, it runs on plain HTTP.

Key features:
1. Loads environment from `.env` (via python-dotenv).
2. Initializes InfluxDB client connection.
3. Reads main config (e.g. logging level) and device config from YAML.
4. Sets Flask `secret_key` from environment variable to secure sessions.
5. Optionally enables HTTPS if `SSL_CERT_FILE` and `SSL_KEY_FILE` are present in environment.

@dependencies
- python-dotenv: for loading .env environment variables.
- backend.db.influx_connector: for InfluxDB initialization.
- backend.app: the Dash app instance (which includes the Flask server).
- utils.config_loader: loads YAML configurations.
- SSL certificates or a reverse proxy for HTTPS (optional).

@notes
- If you don't have valid certificate/key files, the server defaults to HTTP.
- For production usage, consider using a reverse proxy (Nginx/Apache) handling SSL 
  and let this script listen on localhost with HTTP only.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize InfluxDB client
from backend.db.influx_connector import init_influxdb_client
init_influxdb_client()

# Import the Dash app from backend/app.py
from backend.app import app, server

# We'll need our YAML config loader
from utils.config_loader import load_yaml_config

# Load the main config (e.g., logging config)
main_config = load_yaml_config("config/config.yaml")

# Load device/fridge config
devices_config = load_yaml_config("config/devices.yaml")

# Apply logging level from main_config if specified
if main_config and "logging" in main_config and "level" in main_config["logging"]:
    level_str = main_config["logging"]["level"].upper()
    numeric_level = getattr(logging, level_str, logging.INFO)
    logging.getLogger().setLevel(numeric_level)

# Set the Flask secret key from environment or fallback
secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")
server.secret_key = secret_key

if __name__ == "__main__":
    # Read environment variables for host, port, and debug mode
    dash_host = os.getenv("DASH_SERVER_HOST", "0.0.0.0")
    dash_port = int(os.getenv("DASH_SERVER_PORT", "8050"))
    dash_debug = bool(int(os.getenv("DASH_DEBUG", "1")))

    # Optionally set up SSL if environment variables are found
    ssl_cert_file = os.getenv("SSL_CERT_FILE")  # Path to cert file
    ssl_key_file = os.getenv("SSL_KEY_FILE")    # Path to key file

    ssl_context = None
    if ssl_cert_file and ssl_key_file:
        # If both are present, enable HTTPS
        if os.path.isfile(ssl_cert_file) and os.path.isfile(ssl_key_file):
            ssl_context = (ssl_cert_file, ssl_key_file)
            logging.info(f"Using SSL context with cert='{ssl_cert_file}' and key='{ssl_key_file}'.")
        else:
            logging.warning("SSL_CERT_FILE or SSL_KEY_FILE path is invalid. Falling back to HTTP.")

    # Run the Dash server (HTTPS if ssl_context is set, otherwise HTTP)
    app.run_server(
        debug=dash_debug,
        host=dash_host,
        port=dash_port,
        ssl_context=ssl_context
    )
