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
from dash import html

app = dash.Dash(__name__)
server = app.server  # The underlying Flask server

app.layout = html.Div([
    html.H1("Fridge Monitoring Dashboard"),
    html.P("Hello World! This is a minimal starting point for the Dash application.")
])

if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8050) 