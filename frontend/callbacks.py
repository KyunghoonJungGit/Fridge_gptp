"""
@description
Contains Dash callback definitions for:
- Updating the multi-fridge overview data table
- Updating the fridge detail page (graphs, readings)
- Handling command button clicks (e.g. toggles)
- Authenticating user login and controlling UI based on login state

Key features:
1. init_callbacks(app): central function to wire up all callbacks
2. update_overview_table(): updates multi-fridge overview data
3. update_detail_page(): updates detail page graph + readings
4. handle_fridge_commands(): executes backend commands
5. login_callback(): checks username/password, sets Flask session
6. hide_controls_if_not_logged_in(): hides control widgets if user is not logged in

@dependencies
- dash for Input, Output, State, callback_context
- plotly for building graphs
- backend.data_acquisition.fridge_reader
- backend.controllers.command_controller for toggling states
- flask.session for server-side session
- A minimal "fake" user database (USERNAME_PASSWORD) for demonstration

@notes
- In production, you'd replace USERNAME_PASSWORD with a real user database or hashed credential store.
- This is a minimal demonstration of how you might restrict parts of the UI to logged-in users.
"""

from dash import Input, Output, State, html, no_update, dcc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import flask

from backend.data_acquisition import fridge_reader
from backend.controllers.command_controller import execute_command

# A minimal demonstration user "database"
USERNAME_PASSWORD = {
    "admin": "adminpw",
    "labuser": "labpass"
}

def init_callbacks(app):
    """Register all callbacks for both overview, detail pages, command handling, and login."""

    # ---------------------------
    # Multi-fridge overview table and alerts
    # ---------------------------
    @app.callback(
        [Output('fridge-overview-table', 'children'),
         Output('alert-banner', 'children'),
         Output('alert-banner', 'style')],
        Input('poll-interval', 'n_intervals')
    )
    def update_overview_table_and_alerts(_):
        """
        Periodically update the multi-fridge overview table and check for new alerts.
        
        :param _: The current interval tick (unused).
        :return: (Updated table rows, Alert messages, Alert banner style)
        """
        fridge_ids = fridge_reader.get_fridge_ids()

        # Build the fridge overview table
        table_header = [
            html.Tr([
                html.Th("Fridge ID"),
                html.Th("Mix Chamber Temp (K)"),
                html.Th("Lowest Pressure (mbar)"),
                html.Th("State Message"),
                html.Th("Actions")
            ], style={'backgroundColor': '#f2f2f2'})
        ]

        table_rows = []
        for fid in fridge_ids:
            latest = fridge_reader.get_latest_data(fid)
            if not latest:
                table_rows.append(
                    html.Tr([
                        html.Td(fid),
                        html.Td("N/A"),
                        html.Td("N/A"),
                        html.Td("N/A"),
                        html.Td(dcc.Link("View Details", href=f"/fridge/{fid}"))
                    ])
                )
                continue

            sensor_status = latest.get("sensor_status", {})
            mix_temp = sensor_status.get("mix_chamber", "N/A")
            pressures = latest.get("last_pressures_mbar", [])
            lowest_p = min(pressures) if pressures else "N/A"
            state_msg = latest.get("state_message", "N/A")

            row = html.Tr([
                html.Td(fid),
                html.Td(str(mix_temp)),
                html.Td(str(lowest_p)),
                html.Td(state_msg),
                html.Td(dcc.Link("View Details", href=f"/fridge/{fid}"))
            ])
            table_rows.append(row)

        # NEW: Check for new alerts and build alert banner content
        all_alerts = fridge_reader.pop_all_alerts()  # Get and clear all alerts
        
        if all_alerts:  # If we have any alerts
            alert_content = [html.H4("⚠️ New Alerts")]
            
            for fid, alerts in all_alerts.items():
                if alerts:  # Only add fridges with actual alerts
                    alert_content.append(html.H5(f"Fridge: {fid}"))
                    alert_list = html.Ul([
                        html.Li(alert) for alert in alerts
                    ])
                    alert_content.append(alert_list)
            
            # Show the alert banner with yellow background
            alert_style = {
                'backgroundColor': '#ffeb3b',
                'color': '#000',
                'padding': '10px',
                'borderRadius': '5px',
                'marginBottom': '15px',
                'display': 'block'  # Make it visible
            }
            
            return table_header + table_rows, alert_content, alert_style
        else:
            # No alerts, keep the banner hidden
            alert_style = {
                'backgroundColor': '#ffeb3b',
                'color': '#000',
                'padding': '10px',
                'borderRadius': '5px',
                'marginBottom': '15px',
                'display': 'none'  # Keep it hidden
            }
            
            return table_header + table_rows, [], alert_style

    # ---------------------------
    # Fridge detail page updates
    # ---------------------------
    @app.callback(
        [Output('temp-history-graph', 'figure'),
         Output('latest-readings', 'children')],
        [Input('detail-interval', 'n_intervals'),
         Input('hidden-fridge-id', 'children')]
    )
    def update_detail_page(_, fridge_id):
        """
        Update the temperature history graph and latest readings for a specific fridge.
        
        :param _: interval tick (unused).
        :param fridge_id: Which fridge to display.
        :return: (figure, latest-readings-html)
        """
        if not fridge_id:
            return {}, html.P("No fridge selected")

        # Get the latest data from in-memory cache
        latest = fridge_reader.get_latest_data(fridge_id)
        if not latest:
            return {}, html.P("No data available")

        # Generate a simple mock time series for demonstration
        now = datetime.now()
        times = [now - timedelta(minutes=i) for i in range(30, -1, -1)]
        # Start from the current mix chamber reading and vary it slightly over 30 data points
        try:
            mix_current = float(latest['sensor_status'].get('mix_chamber', 300.0))
        except ValueError:
            mix_current = 300.0
        temps = [mix_current + (i * 0.05) for i in range(31)]

        # Create temperature history graph
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=temps,
            mode='lines+markers',
            name='Mix Chamber Temperature'
        ))
        fig.update_layout(
            title=f"Temperature History - {fridge_id}",
            xaxis_title="Time",
            yaxis_title="Temperature (K)"
        )

        # Build a simple table of the latest readings
        sensor_rows = []
        sensor_status = latest.get('sensor_status', {})
        for k, v in sensor_status.items():
            sensor_rows.append(html.Tr([html.Td(k), html.Td(str(v))]))

        sensor_rows.append(
            html.Tr([html.Td("State"), html.Td(latest.get('state_message', 'N/A'))])
        )

        readings_table = html.Table(
            [html.Tr([html.Th("Sensor"), html.Th("Value")])] + sensor_rows,
            style={'width': '100%', 'border': '1px solid #ddd'}
        )

        return fig, readings_table

    # ---------------------------
    # Handle user commands
    # ---------------------------
    @app.callback(
        Output('command-feedback', 'children'),
        [
            Input('toggle-pulsetube-btn', 'n_clicks'),
            Input('toggle-compressor-btn', 'n_clicks'),
            Input('toggle-turbo-btn', 'n_clicks'),
            Input('toggle-valve-btn', 'n_clicks'),
            Input('toggle-heat-switch-btn', 'n_clicks')
        ],
        [
            State('valve-name-input', 'value'),
            State('heat-switch-name-input', 'value'),
            State('hidden-fridge-id', 'children')
        ]
    )
    def handle_fridge_commands(
        pulsetube_clicks,
        compressor_clicks,
        turbo_clicks,
        valve_clicks,
        heat_switch_clicks,
        valve_name,
        heat_switch_name,
        fridge_id
    ):
        """
        Handle user interactions with command buttons on the detail page.
        Identify which button was pressed and execute the corresponding fridge command.
        """
        from dash import callback_context

        if not fridge_id:
            return "No fridge selected, cannot send commands."

        # Identify which input triggered the callback
        triggered_id = None
        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

        # If no button was actually clicked, do nothing
        if not triggered_id:
            return ""

        # Attempt to execute the appropriate command
        if triggered_id == 'toggle-pulsetube-btn':
            ok = execute_command(fridge_id, "toggle_pulsetube")
            return "Pulsetube toggled successfully." if ok else "Failed to toggle pulsetube."

        elif triggered_id == 'toggle-compressor-btn':
            ok = execute_command(fridge_id, "toggle_compressor")
            return "Compressor toggled successfully." if ok else "Failed to toggle compressor."

        elif triggered_id == 'toggle-turbo-btn':
            ok = execute_command(fridge_id, "toggle_turbo")
            return "Turbo toggled successfully." if ok else "Failed to toggle turbo."

        elif triggered_id == 'toggle-valve-btn':
            if not valve_name:
                return "Please enter a valve name."
            ok = execute_command(fridge_id, "toggle_valve", {"valve_name": valve_name})
            return f"Valve '{valve_name}' toggled." if ok else f"Failed to toggle valve '{valve_name}'."

        elif triggered_id == 'toggle-heat-switch-btn':
            if not heat_switch_name:
                return "Please enter a heat switch name."
            ok = execute_command(fridge_id, "toggle_heat_switch", {"heat_switch_name": heat_switch_name})
            return f"Heat switch '{heat_switch_name}' toggled." if ok else f"Failed to toggle heat switch '{heat_switch_name}'."

        return ""

    # ---------------------------
    # Simple login mechanism
    # ---------------------------
    @app.callback(
        [Output('login-error-msg', 'children'),
         Output('url', 'pathname')],
        [Input('login-button', 'n_clicks')],
        [State('login-username', 'value'),
         State('login-password', 'value')]
    )
    def login_callback(n_clicks, username, password):
        """
        Check credentials and set flask.session['logged_in'] if valid.
        If invalid, show error. On success, redirect to the multi-fridge overview.
        """
        if n_clicks is None or n_clicks == 0:
            # No login attempt yet
            return "", no_update

        if not username or not password:
            return "Please enter username and password.", no_update

        # Check credentials
        stored_pw = USERNAME_PASSWORD.get(username)
        if stored_pw and stored_pw == password:
            # Valid credentials
            flask.session['logged_in'] = True
            return "", "/"  # redirect to overview
        else:
            return "Invalid username or password.", no_update

    # ---------------------------
    # Hide/disable controls if not logged in
    # ---------------------------
    @app.callback(
        Output('control-section', 'style'),
        Input('hidden-fridge-id', 'children')
    )
    def hide_controls_if_not_logged_in(_):
        """
        If user is not logged in, hide the entire control section. 
        Otherwise, show it. We rely on Flask session to check login status.
        """
        if not flask.session.get('logged_in', False):
            # Hide it
            return {'display': 'none'}
        # Show it
        return {'display': 'block'}
