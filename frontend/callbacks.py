"""
@description
Contains Dash callback definitions for updating the multi-fridge overview table,
the fridge detail page, handling user commands, and the login mechanism.
Now updated to include minimal color-coded badges next to fridge IDs
and color-coded temperature statuses.

Key features:
1. update_overview_table_and_alerts(): builds a stylized table with badges.
2. update_detail_page(): updates the detail page's graph and readings.
3. handle_fridge_commands(): toggles fridge states via command_controller.
4. login_callback(): verifies credentials and sets session state.
5. hide_controls_if_not_logged_in(): toggles the control UI visibility.

@dependencies
- dash for Input, Output, State, callback_context
- plotly for building graphs
- backend.data_acquisition.fridge_reader for data retrieval
- backend.controllers.command_controller for toggles
- flask.session for server-side session
- The new style classes from assets/style.css

@notes
- We add a small color-coded badge near the fridge ID. If the fridge is 'fridge_1',
  we might choose a green or blue badge; for 'fridge_2', we might show a different color
  or use it to reflect some condition. (For demo, we just use a color-coded approach
  based on fridge index or temperature.)
- We also color the temperature reading if < 300K (badge-green) or >= 300K (badge-red).
"""

from dash import Input, Output, State, html, no_update, dcc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import flask

from backend.data_acquisition import fridge_reader
from backend.controllers.command_controller import execute_command

USERNAME_PASSWORD = {
    "admin": "adminpw",
    "labuser": "labpass"
}

def init_callbacks(app):
    """Register all callbacks for overview, detail pages, command handling, and login."""

    @app.callback(
        [Output('fridge-overview-table', 'children'),
         Output('alert-banner', 'children'),
         Output('alert-banner', 'style')],
        Input('poll-interval', 'n_intervals')
    )
    def update_overview_table_and_alerts(_):
        """
        Periodically update the multi-fridge overview table and check for new alerts.
        We also add color-coded badges for fridge state or ID, and color-coded temperature readings.
        """
        fridge_ids = fridge_reader.get_fridge_ids()

        # Table header row
        table_header = html.Tr([
            html.Th("Fridge ID"),
            html.Th("Mix Chamber Temp (K)"),
            html.Th("Lowest Pressure (mbar)"),
            html.Th("State Message"),
            html.Th("Actions")
        ])

        # Build table rows
        table_rows = []
        for fid in fridge_ids:
            latest = fridge_reader.get_latest_data(fid)
            if not latest:
                row = html.Tr([
                    html.Td(_colored_fridge_id(fid, "badge-red")),
                    html.Td("N/A"),
                    html.Td("N/A"),
                    html.Td("N/A"),
                    html.Td(dcc.Link("View Details", href=f"/fridge/{fid}"))
                ])
                table_rows.append(row)
                continue

            sensor_status = latest.get("sensor_status", {})
            mix_temp_str = sensor_status.get("mix_chamber", "N/A")
            pressures = latest.get("last_pressures_mbar", [])
            lowest_p = min(pressures) if pressures else "N/A"
            state_msg = latest.get("state_message", "N/A")

            # Determine color-coded badge for the fridge ID
            # (For demonstration, we color them based on fridge index)
            color_class = "badge-blue"
            if "1" in fid:
                color_class = "badge-green"
            elif "2" in fid:
                color_class = "badge-yellow"

            # Attempt to parse numeric temp to color-code it
            try:
                mix_temp_val = float(mix_temp_str)
                if mix_temp_val < 300.0:
                    temp_color_class = "badge-green"
                else:
                    temp_color_class = "badge-red"
            except ValueError:
                mix_temp_val = None
                temp_color_class = "badge-yellow"

            # Create a little badge for the temperature reading
            temp_badge = html.Span(
                mix_temp_str,
                className=f"badge {temp_color_class}"
            )

            row = html.Tr([
                html.Td(_colored_fridge_id(fid, color_class)),
                html.Td(temp_badge),
                html.Td(str(lowest_p)),
                html.Td(state_msg),
                html.Td(dcc.Link("View Details", href=f"/fridge/{fid}"))
            ])
            table_rows.append(row)

        # Check for new alerts
        all_alerts = fridge_reader.pop_all_alerts()
        if all_alerts:
            alert_content = [html.H4("⚠️ New Alerts")]
            for afid, alerts in all_alerts.items():
                if alerts:
                    alert_content.append(html.H5(f"Fridge: {afid}"))
                    alert_list = html.Ul([html.Li(alert) for alert in alerts])
                    alert_content.append(alert_list)

            alert_style = {
                'display': 'block',
                'backgroundColor': '#fff'
            }
            return ([table_header] + table_rows), alert_content, alert_style
        else:
            # No alerts
            alert_style = {'display': 'none'}
            return ([table_header] + table_rows), [], alert_style

    @app.callback(
        [Output('temp-history-graph', 'figure'),
         Output('latest-readings', 'children')],
        [Input('detail-interval', 'n_intervals'),
         Input('hidden-fridge-id', 'children')]
    )
    def update_detail_page(_, fridge_id):
        """
        Update the temperature history graph and latest readings for a specific fridge.
        """
        if not fridge_id:
            return {}, html.P("No fridge selected")

        latest = fridge_reader.get_latest_data(fridge_id)
        if not latest:
            return {}, html.P("No data available")

        now = datetime.now()
        times = [now - timedelta(minutes=i) for i in range(30, -1, -1)]

        try:
            mix_current = float(latest['sensor_status'].get('mix_chamber', 300.0))
        except ValueError:
            mix_current = 300.0

        # Create a simple mock trend
        temps = [mix_current + (i * 0.05) for i in range(31)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=temps,
            mode='lines+markers',
            name='Mix Chamber Temperature',
            line=dict(color='#007bff')
        ))
        fig.update_layout(
            title=f"Temperature History - {fridge_id}",
            xaxis_title="Time",
            yaxis_title="Temperature (K)",
            hovermode="x unified"
        )

        # Build table of the latest readings
        sensor_rows = []
        sensor_status = latest.get('sensor_status', {})
        for k, v in sensor_status.items():
            sensor_rows.append(html.Tr([html.Td(k), html.Td(str(v))]))
        sensor_rows.append(
            html.Tr([html.Td("State"), html.Td(latest.get('state_message', 'N/A'))])
        )

        readings_table = html.Table(
            # header
            [html.Tr([html.Th("Sensor"), html.Th("Value")])] + sensor_rows,
            style={'width': '100%', 'border': '1px solid #ddd'}
        )

        return fig, readings_table

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
        Identify which command button was pressed and send the appropriate command to the fridge.
        """
        from dash import callback_context
        if not fridge_id:
            return "No fridge selected, cannot send commands."

        triggered_id = None
        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

        if not triggered_id:
            return ""

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

    @app.callback(
        [Output('login-error-msg', 'children'),
         Output('url', 'pathname')],
        [Input('login-button', 'n_clicks')],
        [State('login-username', 'value'),
         State('login-password', 'value')]
    )
    def login_callback(n_clicks, username, password):
        """
        Simple login: checks username/password, sets session if valid, or shows error otherwise.
        """
        if n_clicks is None or n_clicks == 0:
            return "", no_update

        if not username or not password:
            return "Please enter username and password.", no_update

        stored_pw = USERNAME_PASSWORD.get(username)
        if stored_pw and stored_pw == password:
            flask.session['logged_in'] = True
            return "", "/"
        else:
            return "Invalid username or password.", no_update

    @app.callback(
        Output('control-section', 'style'),
        Input('hidden-fridge-id', 'children')
    )
    def hide_controls_if_not_logged_in(_):
        """
        If the user is not logged in, hide the control section.
        """
        if not flask.session.get('logged_in', False):
            return {'display': 'none'}
        return {'display': 'block'}

def _colored_fridge_id(fid: str, color_class: str):
    """
    Wrap the fridge ID in a color-coded badge for the overview table.
    """
    return html.Span([
        html.Span(fid, className=f"badge {color_class}")
    ])
