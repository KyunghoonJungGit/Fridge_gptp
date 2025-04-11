""" 
@description
Project README describing the Fridge Monitoring system, installation steps, and usage instructions.

Key features:
1. Overview of the project’s purpose and tech stack.
2. Setup instructions (install, run server).
3. Notes on optional HTTPS support and reverse proxy configuration.
4. Explanation of project folder structure and contribution guidelines.

@dependencies
- The entire codebase, environment variables, and optional external tools (InfluxDB, Nginx, Apache).

@notes
- For a production environment, consider using HTTPS via a reverse proxy or 
  self-signed certificate with environment variables for SSL.
"""

# Fridge Monitoring Project

## Overview
This project is a web-based monitoring and control platform for laboratory refrigeration systems (e.g., Bluefors). It uses Plotly Dash to create real-time dashboards, an InfluxDB instance to store and query historical sensor data, and Python-based logic to communicate with simulated or real fridge controllers.

## Folder Structure
- **backend/**: Contains the application logic, data acquisition, controllers, and the main Dash/Flask app.
- **frontend/**: Holds the Dash layouts, callbacks, and UI components.
- **utils/**: Houses utility modules for logging or other shared functionality.
- **data/**: (Optional) If you choose to store data or configuration locally beyond InfluxDB.
- **resources/**: Static resources like images, icons, or custom CSS.
- **tests/**: Contains unit and integration tests.

## Quick Start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
Run the Dash application (HTTP by default):

bash
복사
python run_server.py
Open your browser at http://127.0.0.1:8050 (or http://<your_server_ip>:8050) to access the dashboard.

HTTPS Setup (Optional)
You can run this app under HTTPS in two main ways:

1. Self-Signed or CA-Signed Certificates Directly in Python
Generate or obtain SSL certificate (.crt) and key (.key) files.

Place them somewhere on your server (e.g. /etc/ssl/certs/mycert.crt and /etc/ssl/private/mycert.key).

Set environment variables:

bash
복사
export SSL_CERT_FILE=/etc/ssl/certs/mycert.crt
export SSL_KEY_FILE=/etc/ssl/private/mycert.key
Ensure run_server.py can read those paths. When you run python run_server.py, it will listen on HTTPS at port 8050.

Note: If either file path is invalid or missing, it will fall back to plain HTTP.

2. Reverse Proxy (Nginx or Apache)
For production environments, we recommend using a reverse proxy such as Nginx or Apache to handle HTTPS.
An example (Nginx) configuration snippet:

nginx
복사
server {
    listen 443 ssl;
    server_name fridge-monitor.example.com;

    ssl_certificate /etc/ssl/certs/mycert.crt;
    ssl_certificate_key /etc/ssl/private/mycert.key;

    location / {
        proxy_pass http://127.0.0.1:8050/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
In this setup, the Dash/Flask app runs internally on HTTP (0.0.0.0:8050), and Nginx securely terminates SSL.

Additional Configuration
Environment Variables:

FLASK_SECRET_KEY: A strong secret key used to sign session cookies.

INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET: For InfluxDB connectivity.

DASH_SERVER_HOST, DASH_SERVER_PORT, DASH_DEBUG: Control how the Dash server runs.

SSL_CERT_FILE, SSL_KEY_FILE: (Optional) For direct HTTPS with Flask.

Contributing
Contributions are welcome. Fork this repository, make changes, and submit a pull request.

License
MIT License