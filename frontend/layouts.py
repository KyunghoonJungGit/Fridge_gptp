""" 
@description
Defines the Dash layouts for the Fridge Monitoring dashboard, including:
- A multi-fridge overview page
- A fridge detail page with graphs, info, and command buttons
- A login page for user authentication

Key features:
1. get_overview_layout(): A table listing all fridges, their key readings, and a link to each detail page.
2. get_fridge_detail_layout(fridge_id): Detailed real-time data (graphs, readings) + command widgets.
3. get_login_layout(): Simple username/password form, with a "login-button" to trigger a login callback.

@dependencies
- dash, dash.html, dash.dcc for building the Dash UI
- Python code from the rest of the backend for actual data handling
- The login logic will be implemented in callbacks.py

@notes
- The login form is minimal. In a real system, you'd use hashed passwords and proper security measures.
- The detail page shows controls only if user is logged in (enforced by routes and session checks).
"""

from dash import html, dcc


def get_overview_layout():
    """Return the Dash layout for the multi-fridge overview screen."""
    layout = html.Div([
        html.H2("Multi-Fridge Overview"),
        html.P("Below is a list of all active fridges with their latest temperature, pressure, and status."),
        # Table for fridge overview
        html.Table(
            id='fridge-overview-table',
            style={'border': '1px solid #ccc', 'width': '100%', 'borderCollapse': 'collapse'},
            children=[]  # Updated by callbacks
        ),
        html.Br(),
        # If not logged in, user can navigate to login
        dcc.Link("Login", href="/login", style={'marginRight': '20px'}),
    ], style={'padding': '20px'})
    return layout


def get_fridge_detail_layout(fridge_id: str):
    """
    Returns a Dash layout for a single fridge detail page.
    Includes:
    - Graphs for real-time or historical data
    - Latest readings
    - UI controls to send commands to the fridge (only functional if logged in)
    """

    layout = html.Div([
        # Header with navigation
        html.Div([
            html.H2(f"Fridge Details: {fridge_id}"),
            dcc.Link("Back to Overview", href="/"),
        ], style={'marginBottom': '20px'}),

        # Hidden div storing fridge_id for callbacks
        html.Div(fridge_id, id='hidden-fridge-id', style={'display': 'none'}),

        # Interval for updating detail page data
        dcc.Interval(
            id='detail-interval',
            interval=5000,  # 5 seconds
            n_intervals=0
        ),

        # Graph section
        html.Div([
            html.H3("Temperature History"),
            dcc.Graph(
                id='temp-history-graph',
                figure={}  # Updated by callback
            ),
        ], style={'marginBottom': '20px'}),

        # Latest readings section
        html.Div([
            html.H3("Latest Readings"),
            html.Div(id='latest-readings', children=[])
        ], style={'marginBottom': '20px'}),

        # Command/Control section (shown if logged in)
        # We'll store the style in a Div with an ID to hide/disable if needed
        html.Div([
            html.H3("Fridge Controls"),

            # Row of toggle buttons for main components
            html.Div([
                html.Button("Toggle Pulsetube", id='toggle-pulsetube-btn', n_clicks=0),
                html.Button("Toggle Compressor", id='toggle-compressor-btn', n_clicks=0),
                html.Button("Toggle Turbo", id='toggle-turbo-btn', n_clicks=0),
            ], style={'marginBottom': '10px'}),

            # Controls for toggling a valve
            html.Div([
                html.Label("Valve Name:"),
                dcc.Input(id='valve-name-input', type='text', placeholder='e.g., v5'),
                html.Button("Toggle Valve", id='toggle-valve-btn', n_clicks=0),
            ], style={'marginBottom': '10px'}),

            # Controls for toggling a heat switch
            html.Div([
                html.Label("Heat Switch Name:"),
                dcc.Input(id='heat-switch-name-input', type='text', placeholder='e.g., hs-still'),
                html.Button("Toggle Heat Switch", id='toggle-heat-switch-btn', n_clicks=0),
            ], style={'marginBottom': '10px'}),

            # Command feedback area
            html.Div(id='command-feedback', style={'color': 'blue', 'marginTop': '10px'})
        ], id='control-section'),  # We'll update this div's style in callbacks to hide if not logged in

    ], style={'padding': '20px'})

    return layout


def get_login_layout():
    """
    Returns a Dash layout for a simple login form.
    The user enters username, password, and clicks "Login" to trigger a callback.
    """
    layout = html.Div([
        html.H2("Please Log In"),
        html.Label("Username:"),
        dcc.Input(id='login-username', type='text', placeholder='Username', style={'display': 'block'}),
        html.Label("Password:"),
        dcc.Input(id='login-password', type='password', placeholder='Password', style={'display': 'block', 'marginBottom': '10px'}),
        html.Button("Login", id='login-button', n_clicks=0),
        html.Div(id='login-error-msg', style={'color': 'red', 'marginTop': '10px'}),
        html.Br(),
        dcc.Link("Back to Overview", href="/"),
    ], style={'padding': '20px'})

    return layout
