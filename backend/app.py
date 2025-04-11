"""
@description
Main entry point for the Fridge Monitoring Dash/Flask application.

Key features:
- Initializes a minimal Dash layout for demonstration
- Runs the Dash server on localhost:8050

@notes
- Future steps will expand upon this layout and integrate additional modules
"""

""" 
@description
Main entry point for the Fridge Monitoring Dash/Flask application, now including a /login route.

Key features:
- Sets up a Dash instance
- Routes:
  - "/" => multi-fridge overview
  - "/fridge/<id>" => fridge detail
  - "/login" => login page
- Uses Flask session to determine if user is logged in
- Hides or redirects from certain pages if not authenticated

@dependencies
- dash, dash.html, dash.dcc for the Dash app
- flask.session for server-side session
- python-dotenv for environment variables (loaded in run_server or globally)
- All other project modules that define data acquisition, layout, callbacks

@notes
- If a user tries to access /fridge/<id> but isn't logged in, we show a short message or redirect to /login.
- The app checks session state in the URL routing callback.
"""

import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import flask

from backend.data_acquisition.fridge_reader import init_fridges, poll_all_fridges, get_fridge_ids
from frontend.layouts import (
    get_overview_layout,
    get_fridge_detail_layout,
    get_login_layout
)
from frontend.callbacks import init_callbacks

# Initialize dummy fridges
init_fridges()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Expose the Flask server for session handling

# Define the base layout with URL routing
app.layout = html.Div([
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
])

# URL routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """
    Route to different pages based on URL pathname.
    If the user is not logged in and tries to access a restricted page, 
    redirect or show a message prompting them to log in.
    """
    # For easy check: user logged_in status from Flask session
    is_logged_in = flask.session.get('logged_in', False)

    # Routing logic
    if pathname in ('', '/', '/overview'):
        # Show multi-fridge overview (accessible to anyone, even if not logged in)
        return get_overview_layout()

    elif pathname == '/login':
        # Show login page
        return get_login_layout()

    elif pathname and pathname.startswith('/fridge/'):
        # If not logged in, show a "please log in" message or redirect
        if not is_logged_in:
            return html.Div([
                html.H2("Access Denied - Please Log In"),
                dcc.Link("Go to Login", href="/login")
            ])

        # Otherwise, parse the fridge_id
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

# Initialize callbacks (for overview, detail pages, commands, login)
init_callbacks(app)

# Background polling callback
@app.callback(
    Output('poll-interval', 'disabled'),  # Dummy output to keep callback running
    Input('poll-interval', 'n_intervals')
)
def trigger_polling(_):
    """
    Poll all fridges in the background every interval.
    Writes or caches data internally. 
    By returning False, we keep the interval active.
    """
    poll_all_fridges()
    return False

if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8050) 