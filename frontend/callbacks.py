"""
@description
Contains Dash callback definitions for updating the multi-fridge overview data
and detail page graphs.
"""

from dash import Input, Output, State, html
import dash_core_components as dcc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from backend.data_acquisition import fridge_reader

def init_callbacks(app):
    """Register all callbacks for both overview and detail pages."""

    @app.callback(
        Output('fridge-overview-table', 'children'),
        Input('poll-interval', 'n_intervals')
    )
    def update_overview_table(_):
        """Update the multi-fridge overview table."""
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
        """Update the temperature history graph and latest readings."""
        if not fridge_id:
            return {}, html.P("No fridge selected")

        # Get latest data for this fridge
        latest = fridge_reader.get_latest_data(fridge_id)
        if not latest:
            return {}, html.P("No data available")

        # Create a mock time series for demonstration
        # In production, this would come from InfluxDB
        now = datetime.now()
        times = [now - timedelta(minutes=i) for i in range(30, -1, -1)]
        temps = [float(latest['sensor_status'].get('mix_chamber', 0)) + i*0.1 for i in range(31)]

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

        # Create latest readings display
        readings = html.Div([
            html.Table([
                html.Tr([html.Th("Sensor"), html.Th("Value")]),
                *[
                    html.Tr([html.Td(k), html.Td(str(v))])
                    for k, v in latest['sensor_status'].items()
                ],
                html.Tr([html.Td("State"), html.Td(latest.get('state_message', 'N/A'))])
            ], style={'width': '100%', 'border': '1px solid #ddd'})
        ])

        return fig, readings
