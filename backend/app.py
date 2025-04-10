"""
@description
Main entry point for the Fridge Monitoring Dash/Flask application.

Key features:
- Initializes a minimal Dash layout for demonstration
- Runs the Dash server on localhost:8050

@notes
- Future steps will expand upon this layout and integrate additional modules
"""

import dash
from dash import html, dcc
from dash.dependencies import Input, Output

from backend.data_acquisition.fridge_reader import init_fridges, poll_all_fridges

# Initialize the dummy fridges
init_fridges()

app = dash.Dash(__name__)
server = app.server  # The underlying Flask server

# Simple layout:
# 1) A heading
# 2) A message
# 3) An Interval component set to 1-second intervals
# 4) A 'div' to display a poll status message
app.layout = html.Div([
    html.H1("Fridge Monitoring Dashboard"),
    html.P("Hello World! This is a minimal Dash application."),

    # Interval for real-time polling (1000 ms = 1 second)
    dcc.Interval(
        id='poll-interval',
        interval=1000,  # 1 second
        n_intervals=0
    ),

    html.Div(id='poll-status', style={"marginTop": "20px", "fontWeight": "bold"})
])


@app.callback(
    Output('poll-status', 'children'),
    Input('poll-interval', 'n_intervals')
)
def trigger_polling(n_calls):
    """
    This callback is invoked every time the Interval fires (every 1 second).
    It calls poll_all_fridges() to retrieve updated data from all dummy fridge instances
    and store it in InfluxDB.
    We return a status string indicating how many times the poll has run.
    """
    poll_all_fridges()
    return f"Polling iteration #{n_calls}. Data written to InfluxDB."

if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8050) 