"""
@description
Defines the Dash layouts for the Fridge Monitoring dashboard, including:
- A multi-fridge overview page
- A fridge detail page with graphs and info
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
            children=[]  # Initial empty children
        ),
    ], style={'padding': '20px'})
    return layout

def get_fridge_detail_layout(fridge_id: str):
    """
    Returns a Dash layout for a single fridge detail page.
    Includes graphs and detailed information.
    """
    layout = html.Div([
        # Header with navigation
        html.Div([
            html.H2(f"Fridge Details: {fridge_id}"),
            dcc.Link("Back to Overview", href="/"),
        ], style={'marginBottom': '20px'}),

        # Store fridge_id for callbacks
        html.Div(fridge_id, id='hidden-fridge-id', style={'display': 'none'}),

        # Interval for updating graphs
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
            html.Div(id='latest-readings', children=[])  # Initial empty children
        ]),
    ], style={'padding': '20px'})
    
    return layout
