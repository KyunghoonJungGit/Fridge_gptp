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

from backend.data_acquisition.fridge_reader import init_fridges, poll_all_fridges, get_fridge_ids
from frontend.layouts import get_overview_layout, get_fridge_detail_layout
from frontend.callbacks import init_callbacks

# Initialize dummy fridges
init_fridges()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Define the base layout with URL routing
app.layout = html.Div([
    # URL Location component for routing
    dcc.Location(id='url', refresh=False),
    
    # Main content div that will be updated based on URL
    html.Div(id='page-content'),

    # Background polling interval
    dcc.Interval(
        id='poll-interval',
        interval=1000,  # 1 second
        n_intervals=0
    ),
])

# URL routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route to different pages based on URL pathname"""
    if pathname == '/' or pathname == '':
        return get_overview_layout()
    elif pathname and pathname.startswith('/fridge/'):
        fridge_id = pathname.split('/fridge/')[-1]
        if fridge_id in get_fridge_ids():
            return get_fridge_detail_layout(fridge_id)
        return html.Div([html.H2("Error: Invalid fridge ID"), dcc.Link("Back to Overview", href="/")])
    else:
        return html.Div([html.H2("404 - Page not found"), dcc.Link("Back to Overview", href="/")])

# Initialize all callbacks
init_callbacks(app)

# Background polling callback
@app.callback(
    Output('poll-interval', 'disabled'),  # Dummy output to keep callback running
    Input('poll-interval', 'n_intervals')
)
def trigger_polling(_):
    """Poll all fridges in the background"""
    poll_all_fridges()
    return False  # Keep the interval enabled

if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8050) 