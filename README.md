# Fridge Monitoring Project

## Overview
This project is a web-based monitoring and control platform for laboratory refrigeration systems (e.g., Bluefors). It uses Plotly Dash to create real-time dashboards, an InfluxDB instance to store and query historical sensor data, and Python-based logic to communicate with simulated or real fridge controllers.

## Folder Structure
- **backend/**: Contains the application logic, data acquisition, controllers, and the main Dash/Flask app.
- **frontend/**: Holds the Dash layouts, callbacks, and UI components.
- **utils/**: Houses utility modules for logging or other shared functionality.
- **data/**: Stores data or configuration files as needed.
- **resources/**: Static resources like images, icons, or custom CSS.

## Quick Start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Dash application:
   ```bash
   python backend/app.py
   ```
3. Open your browser at `http://127.0.0.1:8050` to access the dashboard.

## Contributing
Contributions are welcome. Fork this repository, make changes, and submit a pull request.

## License
[MIT License](https://opensource.org/licenses/MIT) 