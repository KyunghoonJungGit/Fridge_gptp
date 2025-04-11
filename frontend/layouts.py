"""
@description
Defines the Dash layouts for the Fridge Monitoring dashboard,
including a multi-fridge overview page, a fridge detail page,
and a login page. Now updated with improved styling and minimal
color-coded badges.

Key features:
1. get_overview_layout(): A table listing all fridges with colored badges.
2. get_fridge_detail_layout(fridge_id): 
   - Historical graph
   - Latest readings
   - Control buttons with consistent styling.
3. get_login_layout(): A simple login form.

@dependencies
- dash, dash.html, dash.dcc for building the Dash UI
- The new CSS in assets/style.css for styling
- Minimal references to the rest of the code

@notes
- The <table> elements now have className="overview-table" for styling.
- We incorporate color-coded badges for fridge states or statuses.
"""

from dash import html, dcc

def get_overview_layout():
    """Return the Dash layout for the multi-fridge overview screen."""
    layout = html.Div([
        html.H2("Multi-Fridge Overview", style={'marginTop': '10px'}),

        # Alert banner for newly detected alerts
        html.Div(
            id='alert-banner',
            style={
                'display': 'none'  # visible when we have alerts
            },
            children=[]
        ),

        html.P("Below is a list of all active fridges with their latest temperature, pressure, and status."),

        # Table for fridge overview (callback updates the table content)
        html.Table(
            id='fridge-overview-table',
            className="overview-table",  # link to our CSS
            children=[]
        ),

        # Login link
        html.Div([
            dcc.Link("Login", href="/login", style={'marginRight': '20px'})
        ], style={'marginTop': '10px'})
    ], style={'padding': '20px'})
    return layout


def get_fridge_detail_layout(fridge_id: str):
    """
    Returns a Dash layout for a single fridge detail page,
    with a graph, sensor readings, and command widgets.
    """
    layout = html.Div([
        # Header with navigation
        html.Div([
            html.H2(f"Fridge Details: {fridge_id}"),
            dcc.Link("Back to Overview", href="/")
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
                figure={}
            ),
        ], style={'marginBottom': '20px'}),

        # Latest readings section
        html.Div([
            html.H3("Latest Readings"),
            html.Div(id='latest-readings', children=[])
        ], style={'marginBottom': '20px'}),

        # Command/Control section (only if logged in)
        html.Div([
            html.H3("Fridge Controls"),

            # Row of toggle buttons for main components
            html.Div([
                html.Button("Toggle Pulsetube", id='toggle-pulsetube-btn', n_clicks=0),
                html.Button("Toggle Compressor", id='toggle-compressor-btn', n_clicks=0),
                html.Button("Toggle Turbo", id='toggle-turbo-btn', n_clicks=0),
            ], style={'marginBottom': '10px'}),

            # Valve
            html.Div([
                html.Label("Valve Name:", style={'marginRight': '6px'}),
                dcc.Input(id='valve-name-input', type='text', placeholder='e.g., v5'),
                html.Button("Toggle Valve", id='toggle-valve-btn', n_clicks=0),
            ], style={'marginBottom': '10px'}),

            # Heat Switch
            html.Div([
                html.Label("Heat Switch Name:", style={'marginRight': '6px'}),
                dcc.Input(id='heat-switch-name-input', type='text', placeholder='e.g., hs-still'),
                html.Button("Toggle Heat Switch", id='toggle-heat-switch-btn', n_clicks=0),
            ], style={'marginBottom': '10px'}),

            # Command feedback area
            html.Div(id='command-feedback', style={'color': 'blue', 'marginTop': '10px'})
        ], id='control-section'),

    ], style={'padding': '20px'})

    return layout


def get_login_layout():
    """
    A Dash layout for a simple login form.
    """
    layout = html.Div([
        html.H2("Please Log In", style={'marginTop': '10px'}),
        html.Label("Username:"),
        dcc.Input(id='login-username', type='text', placeholder='Username',
                  style={'display': 'block', 'marginBottom': '6px'}),
        html.Label("Password:"),
        dcc.Input(id='login-password', type='password', placeholder='Password',
                  style={'display': 'block', 'marginBottom': '10px'}),
        html.Button("Login", id='login-button', n_clicks=0),
        html.Div(id='login-error-msg', style={'color': 'red', 'marginTop': '10px'}),
        html.Br(),
        dcc.Link("Back to Overview", href="/"),
    ], style={'padding': '20px'})
    return layout
