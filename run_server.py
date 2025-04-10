"""
@description
Entry-point script for running the Dash/Flask server. Loads environment variables,
reads YAML config, and starts the web application.

Key features:
- Uses python-dotenv to load .env
- Loads main config and device config from YAML
- Sets Flask secret key (for session security) from environment
- Imports the Dash app from backend/app.py and runs it

@dependencies
- python-dotenv: to load .env
- utils/config_loader: to load YAML config
- backend.app: contains the Dash app and server instance

@notes
- Once the server starts, visit http://127.0.0.1:8050 in a browser to see the dashboard.
- Adjust "host" or "port" as needed (e.g., to 0.0.0.0 if you want external access).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize InfluxDB client
from backend.db.influx_connector import init_influxdb_client
init_influxdb_client()

# Load the Dash app from backend/app.py
# By convention, app.py sets app = dash.Dash(__name__) and server = app.server
from backend.app import app, server

# We'll need our YAML config loader
from utils.config_loader import load_yaml_config

# Load the main config (e.g., logging config, etc.)
main_config = load_yaml_config("config/config.yaml")

# Load device/fridge config
devices_config = load_yaml_config("config/devices.yaml")

# Here we can do something with these configs if needed
# e.g., set a logging level from main_config['logging']['level'], etc.
import logging

if main_config and "logging" in main_config and "level" in main_config["logging"]:
    level_str = main_config["logging"]["level"].upper()
    numeric_level = getattr(logging, level_str, logging.INFO)
    logging.getLogger().setLevel(numeric_level)

# Set the Flask secret key from environment
secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")
server.secret_key = secret_key

if __name__ == "__main__":
    # Run the Dash server
    app.run_server(debug=True, host="127.0.0.1", port=8050)
