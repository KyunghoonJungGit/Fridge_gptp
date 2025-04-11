"""
@description
Main entry point for the Fridge Monitoring Dash/Flask application.
Includes:
- Dash-based pages and callbacks for the web UI
- New API endpoints for remote fridge data retrieval and commands

Key features:
1. Dash routes: (/, /login, /fridge/<id>)
2. Periodic polling callback to gather updated fridge data
3. Two new JSON API endpoints:
   - GET /api/fridge/<fridge_id>/latest
   - POST /api/fridge/<fridge_id>/command
4. Flask session-based login for web UI (not strictly required for the new API)

@dependencies
- dash, dash.html, dash.dcc for the Dash UI
- flask for serving requests, managing sessions
- requests library is not used here (the client library uses requests)
- backend.data_acquisition.fridge_reader for fridge data
- backend.controllers.command_controller for commands

@notes
- The new JSON endpoints allow external scripts or the python_client library
  to get the latest fridge info and send commands remotely.
- No authentication is enforced for these endpoints in this minimal example.
"""
"""
@description
Main entry point for the Fridge Monitoring Dash/Flask application.
"""

import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import flask
from flask import request, jsonify

from backend.data_acquisition.fridge_reader import (
    init_fridges,
    poll_all_fridges,
    get_fridge_ids,
    get_latest_data
)
from frontend.layouts import (
    get_overview_layout,
    get_fridge_detail_layout,
    get_login_layout
)
from frontend.callbacks import init_callbacks
from backend.controllers.command_controller import execute_command

# Initialize dummy fridges
init_fridges()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Expose the Flask server for session handling

# Define the base layout with theme container + top-right toggle
app.layout = html.Div(
    id="theme-container",
    className="light-theme",  # default
    children=[
        # Hidden store that remembers which theme is currently selected
        dcc.Store(id="theme-store", data="light-theme"),

        # A simple top bar that includes the "Dark Mode" toggle button
        html.Div(
            style={"textAlign": "right", "padding": "10px"},
            children=[
                html.Button(
                    "🌙",  # moon icon
                    id="theme-toggle-button",
                    title="Toggle Dark Mode",
                    style={
                        "fontSize": "18px",
                        "cursor": "pointer",
                        "backgroundColor": "transparent",
                        "border": "none",
                        "outline": "none"
                    }
                ),
            ]
        ),

        # URL Location component for routing
        dcc.Location(id='url', refresh=False),
        
        # Main content div that will be updated based on URL
        html.Div(id='page-content'),

        # Background polling interval for fridge data
        dcc.Interval(
            id='poll-interval',
            interval=1000,  # 1 second
            n_intervals=0
        ),
    ]
)

# URL routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    # Check if user is logged in
    is_logged_in = flask.session.get('logged_in', False)

    if pathname in ('', '/', '/overview'):
        return get_overview_layout()
    elif pathname == '/login':
        return get_login_layout()
    elif pathname and pathname.startswith('/fridge/'):
        if not is_logged_in:
            return html.Div([
                html.H2("Access Denied - Please Log In"),
                dcc.Link("Go to Login", href="/login")
            ])
        fridge_id = pathname.split('/fridge/')[-1]
        if fridge_id in get_fridge_ids():
            return get_fridge_detail_layout(fridge_id)
        return html.Div([
            html.H2("Error: Invalid fridge ID"),
            dcc.Link("Back to Overview", href="/")
        ])
    else:
        return html.Div([
            html.H2("404 - Page not found"),
            dcc.Link("Back to Overview", href="/")
        ])

# Initialize all Dash callbacks
init_callbacks(app)

# Background polling callback
@app.callback(
    Output('poll-interval', 'disabled'),
    Input('poll-interval', 'n_intervals')
)
def trigger_polling(_):
    poll_all_fridges()
    return False


# JSON API Endpoints
@server.route('/api/fridge/<fridge_id>/latest', methods=['GET'])
def api_get_fridge_latest(fridge_id):
    try:
        if fridge_id not in get_fridge_ids():
            return jsonify({"success": False, "error": "Invalid fridge_id"}), 400
        data = get_latest_data(fridge_id)
        if not data:
            return jsonify({"success": False, "error": "No data available"}), 404
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@server.route('/api/fridge/<fridge_id>/command', methods=['POST'])
def api_post_fridge_command(fridge_id):
    try:
        if fridge_id not in get_fridge_ids():
            return jsonify({"success": False, "error": "Invalid fridge_id"}), 400
        json_body = request.get_json(force=True, silent=True) or {}
        command = json_body.get("command", "").strip()
        params = json_body.get("params", {})

        if not command:
            return jsonify({"success": False, "error": "Missing command"}), 400

        result = execute_command(fridge_id, command, params)
        if result:
            return jsonify({"success": True, "message": "Command executed successfully"}), 200
        else:
            return jsonify({"success": False, "message": "Command execution failed"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8050)
