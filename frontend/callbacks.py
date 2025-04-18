"""
@description
Contains Dash callback definitions for:
- Updating the multi-fridge overview table
- Displaying new alerts
- Showing/hiding the detail page
- Handling user commands
- Logging in (session-based)
- Toggling the theme (light/dark)
- Dynamically updating the login/logout link text

Key features:
1. update_overview_table_and_alerts(): builds a stylized table
2. update_detail_page(): updates detail page with timeseries from InfluxDB
3. handle_fridge_commands(): sets temperature/resistance
4. login_callback(): verifies credentials
5. hide_controls_if_not_logged_in(): toggles control UI
6. toggle_theme(): toggles between light and dark
7. update_login_logout_link(): changes link text from "Login" to "Logout" when logged in

@dependencies
- dash for UI and callback context
- flask for session
- backend.fridge_state for fridge data
- backend.controllers.command_controller for set_temp/set_resist
- backend.db.influx_connector for data queries (Plotly timeseries)

@notes
- The link for logout is an html.A in layouts.py, which ensures a real HTTP GET request to /logout.
- The detail page was previously hard-coded to query "my-bucket". Now we fetch the actual bucket
  from backend.db.influx_connector.get_influx_bucket() so it matches the environment settings.
"""

from dash import Input, Output, State, html, no_update, dcc, callback_context
import plotly.graph_objects as go
from datetime import datetime
import flask

from backend.fridge_state import (
    get_fridge_ids,
    get_latest_data,
    poll_all_fridges,
    pop_all_alerts
)
from backend.controllers.command_controller import execute_command

# NEW: We import get_influx_bucket from the influx_connector
from backend.db.influx_connector import query_data, get_influx_bucket

USERNAME_PASSWORD = {
    "admin": "adminpw",
    "labuser": "labpass"
}

def init_callbacks(app):
    """Register all callbacks for overview, detail pages, commands, login, logout link, and theme toggling."""

    @app.callback(
        [Output('fridge-overview-table', 'children'),
         Output('alert-banner', 'children'),
         Output('alert-banner', 'style')],
        Input('poll-interval', 'n_intervals')
    )
    def update_overview_table_and_alerts(_):
        fridge_ids = get_fridge_ids()

        table_header = html.Tr([
            html.Th("Fridge ID"),
            html.Th("Mix Chamber Temp (K)"),
            html.Th("Lowest Pressure (mbar)"),
            html.Th("State Message"),
            html.Th("Actions")
        ])

        table_rows = []
        for fid in fridge_ids:
            latest = get_latest_data(fid)
            row = None
            if not latest:
                row = html.Tr([
                    html.Td(_colored_fridge_id(fid, "badge-red")),
                    html.Td("N/A"),
                    html.Td("N/A"),
                    html.Td("N/A"),
                    html.Td(dcc.Link("View Details", href=f"/fridge/{fid}"))
                ])
            else:
                sensor_status = latest.get("sensor_status", {})
                mix_temp_str = sensor_status.get("mix_chamber", "N/A")
                pressures = latest.get("last_pressures_mbar", [])
                lowest_p = min(pressures) if pressures else "N/A"
                state_msg = latest.get("state_message", "N/A")

                # Badge color by fridge ID
                if "1" in fid:
                    fid_badge_class = "badge-green"
                elif "2" in fid:
                    fid_badge_class = "badge-yellow"
                else:
                    fid_badge_class = "badge-blue"

                # Temperature color badge
                try:
                    mix_val = float(mix_temp_str)
                    temp_badge_class = "badge-green" if mix_val < 300 else "badge-red"
                except ValueError:
                    temp_badge_class = "badge-yellow"

                row = html.Tr([
                    html.Td(_colored_fridge_id(fid, fid_badge_class)),
                    html.Td(html.Span(mix_temp_str, className=f"badge {temp_badge_class}")),
                    html.Td(str(lowest_p)),
                    html.Td(state_msg),
                    html.Td(dcc.Link("View Details", href=f"/fridge/{fid}"))
                ])
            table_rows.append(row)

        # Check for new alerts
        all_alerts = pop_all_alerts()
        if all_alerts:
            alert_content = [html.H4("⚠️ New Alerts")]
            for afid, alerts in all_alerts.items():
                if alerts:
                    alert_content.append(html.H5(f"Fridge: {afid}"))
                    alert_list = html.Ul([html.Li(a) for a in alerts])
                    alert_content.append(alert_list)

            banner_style = {
                'display': 'block',
                'backgroundColor': '#fff'
            }
            return ([table_header] + table_rows), alert_content, banner_style
        else:
            banner_style = {'display': 'none'}
            return ([table_header] + table_rows), [], banner_style

    @app.callback(
        [Output('temp-history-graph', 'figure'),
         Output('latest-readings', 'children')],
        [Input('detail-interval', 'n_intervals'),
         Input('hidden-fridge-id', 'children'),
         Input('theme-store', 'data')]
    )
    def update_detail_page(_, fridge_id, current_theme):
        """
        Renders the temperature history graph and latest readings for a single fridge.
        Queries the bucket specified in the environment (via get_influx_bucket).
        """
        if not fridge_id:
            return {}, html.P("No fridge selected")

        latest = get_latest_data(fridge_id)
        if not latest:
            return {}, html.P("No data available")

        bucket_name = get_influx_bucket()  # Use the actual bucket

        # Build a Flux query targeting the user’s configured bucket.
        flux = f'''
        from(bucket: "{bucket_name}")
          |> range(start: -30m)
          |> filter(fn: (r) => r._measurement == "fridge_data")
          |> filter(fn: (r) => r.fridge_id == "{fridge_id}")
          |> filter(fn: (r) => r._field == "temp_chA")
          |> keep(columns: ["_time", "_value"])
          |> sort(columns: ["_time"])
        '''
        rows = query_data(flux)

        if rows:
            times = [r["time"] for r in rows]
            temps = [r["_value"] for r in rows]
        else:
            # Fallback if no data from Influx
            now = datetime.now()
            try:
                mix_current = float(latest['sensor_status'].get('mix_chamber', 300.0))
            except ValueError:
                mix_current = 300.0
            times = [now]
            temps = [mix_current]

        # Theme-based colors
        if current_theme == "dark-theme":
            paper_bg, plot_bg, font_col = "#1e1e1e", "#2b2b2b", "#f0f0f0"
        else:
            paper_bg, plot_bg, font_col = "#f8f9fa", "#ffffff", "#333333"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=temps,
            mode='lines+markers',
            name='Mix‑Chamber (chA)',
            line=dict(color='#007bff')
        ))
        fig.update_layout(
            title=f"Temperature History – {fridge_id}",
            xaxis_title="Time",
            yaxis_title="Temperature (K)",
            hovermode="x unified",
            paper_bgcolor=paper_bg,
            plot_bgcolor=plot_bg,
            font=dict(color=font_col)
        )

        # Latest readings table
        sensor_rows = [
            html.Tr([html.Td(k), html.Td(str(v))])
            for k, v in latest.get('sensor_status', {}).items()
        ]
        sensor_rows.append(html.Tr([html.Td("State"),
                                    html.Td(latest.get('state_message', 'N/A'))]))

        readings_table = html.Table(
            [html.Tr([html.Th("Sensor"), html.Th("Value")])] + sensor_rows,
            style={'width': '100%', 'border': '1px solid #ddd'}
        )
        return fig, readings_table

    @app.callback(
        Output('command-feedback', 'children'),
        [
            Input('set-temp-btn', 'n_clicks'),
            Input('set-resist-btn', 'n_clicks')
        ],
        [
            State('temp-channel-input', 'value'),
            State('temp-value-input', 'value'),
            State('resist-channel-input', 'value'),
            State('resist-value-input', 'value'),
            State('hidden-fridge-id', 'children')
        ]
    )
    def handle_fridge_commands(
        set_temp_clicks,
        set_resist_clicks,
        temp_channel,
        temp_value,
        resist_channel,
        resist_value,
        fridge_id
    ):
        """
        Called when user presses "Set Temperature" or "Set Resistance" button on detail page.
        """
        if not fridge_id:
            return "No fridge selected, cannot send commands."

        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        else:
            triggered_id = None

        if not triggered_id:
            return ""

        if triggered_id == 'set-temp-btn':
            if not temp_channel or not temp_value:
                return "Please enter channel and temperature value."
            result = execute_command(fridge_id, "set_temp", {"channel": temp_channel, "value": temp_value})
            return "Temperature set successfully." if result else "Failed to set temperature."

        elif triggered_id == 'set-resist-btn':
            if not resist_channel or not resist_value:
                return "Please enter channel and resistance value."
            result = execute_command(fridge_id, "set_resist", {"channel": resist_channel, "value": resist_value})
            return "Resistance set successfully." if result else "Failed to set resistance."

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
        Called when the user clicks the login button on the login page.
        Verifies credentials and sets session['logged_in'] = True if valid.
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
        Hides the temp/resistance control UI if the user is not logged in.
        """
        if not flask.session.get('logged_in', False):
            return {'display': 'none'}
        return {'display': 'block'}

    # Theme toggling
    @app.callback(
        Output("theme-store", "data"),
        Input("theme-toggle-button", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True
    )
    def toggle_theme(n_clicks, current_theme):
        if n_clicks is None:
            return current_theme
        return "dark-theme" if current_theme == "light-theme" else "light-theme"

    @app.callback(
        Output("theme-container", "className"),
        Input("theme-store", "data")
    )
    def set_container_class(current_theme):
        return current_theme

    @app.callback(
        [Output('login-logout-link', 'children'),
         Output('login-logout-link', 'href')],
        Input('url', 'pathname')
    )
    def update_login_logout_link(_pathname):
        """
        Observes changes in URL.
        If session indicates 'logged_in', show "Logout" linking to /logout.
        Otherwise, show "Login" linking to /login.
        """
        if flask.session.get('logged_in', False):
            return ("Logout", "/logout")
        else:
            return ("Login", "/login")

def _colored_fridge_id(fid: str, color_class: str):
    """Helper function to render a fridge ID with a color-coded badge."""
    return html.Span([
        html.Span(fid, className=f"badge {color_class}")
    ])
