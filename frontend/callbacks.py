"""
@description
Contains Dash callback definitions for:
- Updating the multi-fridge overview data table
- Updating the fridge detail page (graphs, readings)
- Handling command button clicks (e.g., toggling the pulse tube, compressor, valves, etc.)

Key features:
1. init_callbacks(app): central function to wire up all callbacks
2. update_overview_table(...): updates the overview table periodically
3. update_detail_page(...): updates the detail page graph and readings
4. handle_fridge_commands(...): processes button clicks for toggles or set_channel commands

@dependencies
- dash for Input, Output, State
- plotly for building graphs
- backend.data_acquisition.fridge_reader to fetch data
- backend.controllers.command_controller to execute commands

@notes
- The new callback handle_fridge_commands is triggered by multiple Input components (button clicks).
  We identify which button fired using dash.callback_context and proceed accordingly.
- For demonstration, the code uses a mock time series for the temperature graph; in production,
  we'd query InfluxDB or another data source for historical data.
"""

from dash import Input, Output, State, html
import dash_core_components as dcc
import plotly.graph_objects as go
from datetime import datetime, timedelta

from backend.data_acquisition import fridge_reader
from backend.controllers.command_controller import execute_command


def init_callbacks(app):
    """Register all callbacks for both overview and detail pages."""

    @app.callback(
        Output('fridge-overview-table', 'children'),
        Input('poll-interval', 'n_intervals')
    )
    def update_overview_table(_):
        """
        Periodically update the multi-fridge overview table.
        
        :param _: The current interval tick (unused).
        :return: The updated table rows with fridge info.
        """
        fridge_ids = fridge_reader.get_fridge_ids()

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

        return table_header + table_rows

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
        mix_current = float(latest['sensor_status'].get('mix_chamber', 300.0))
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
        We figure out which button was pressed by checking the changed_id from dash.callback_context.

        :param pulsetube_clicks: # times "Toggle Pulsetube" was clicked
        :param compressor_clicks: # times "Toggle Compressor" was clicked
        :param turbo_clicks: # times "Toggle Turbo" was clicked
        :param valve_clicks: # times "Toggle Valve" was clicked
        :param heat_switch_clicks: # times "Toggle Heat Switch" was clicked
        :param valve_name: the user-entered valve name
        :param heat_switch_name: the user-entered heat switch name
        :param fridge_id: which fridge to control
        :return: a string message about success or failure of the command
        """
        from dash import callback_context

        if not fridge_id:
            return "No fridge selected, cannot send commands."

        # Identify which input triggered the callback
        triggered_id = None
        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

        # If no button was actually clicked or there's no triggered_id, do nothing
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

        # Default (shouldn't happen)
        return ""
