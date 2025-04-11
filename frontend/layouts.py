""" 
@description
Defines the Dash layouts for the Fridge Monitoring dashboard, including:
- A multi-fridge overview page
- A fridge detail page with graphs, info, and command buttons

Key features:
1. get_overview_layout(): Displays a table listing all fridges, their key readings, and a link to each detail page.
2. get_fridge_detail_layout(): Shows:
   - Real-time data graphs
   - Latest readings
   - Control widgets (buttons, inputs) to issue commands to the backend

@dependencies
- dash, dash.html, dash.dcc: for building the Dash UI
- Python code from the rest of the backend for actual data handling

@notes
- The new command widgets allow toggling major components (pulse tube, compressor, turbo)
  and also allow toggling valves and heat switches with user-provided names.
- Layout is kept simple with minimal styling.
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
            children=[]  # Initial empty children, will be updated by callbacks
        ),
    ], style={'padding': '20px'})
    return layout


def get_fridge_detail_layout(fridge_id: str):
    """
    Returns a Dash layout for a single fridge detail page.
    Includes:
    - Graphs for real-time or historical data
    - Latest readings
    - UI controls to send commands to the fridge
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
                figure={}  # Initial empty figure
            ),
        ], style={'marginBottom': '20px'}),

        # Latest readings section
        html.Div([
            html.H3("Latest Readings"),
            html.Div(id='latest-readings', children=[])
        ], style={'marginBottom': '20px'}),

        # Command/Control section
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
        ])
    ], style={'padding': '20px'})

    return layout
