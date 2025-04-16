"""
@description
Defines the Dash layouts for the Fridge Monitoring dashboard,
including a multi-fridge overview page, a fridge detail page,
and a login page.

Key features:
1. get_overview_layout(): A table listing all fridges with colored badges.
2. get_fridge_detail_layout(fridge_id): 
   - Historical graph
   - Latest readings
   - Control inputs for set_temp and set_resist
3. get_login_layout(): A simple login form

@dependencies
- dash, dash.html, dash.dcc for building the Dash UI
- The new CSS in assets/style.css for styling
- Minimal references to the rest of the code

@notes
- We have replaced toggles (like "Toggle Pulsetube") with "Set Temperature" / "Set Resistance" 
- We include input fields for channel and value, plus the relevant buttons.
"""

from dash import html, dcc

def get_overview_layout():
    layout = html.Div([
        html.H2("Multi-Fridge Overview", style={'marginTop': '10px'}),
        html.Div(
            id='alert-banner',
            style={'display': 'none'},  # We'll rely on theme CSS
            children=[]
        ),
        html.P("Below is a list of all active fridges..."),
        html.Table(
            id='fridge-overview-table',
            className="overview-table",
            children=[]
        ),
        html.Div([
            dcc.Link("Login", href="/login", style={
                'marginRight': '20px',
                'color': '#007bff',
                'textDecoration': 'none',
                'fontWeight': '600'
            })
        ], style={'marginTop': '20px'})
    ], style={'padding': '20px'})
    return layout

def get_fridge_detail_layout(fridge_id: str):
    layout = html.Div([
        # Header
        html.Div([
            html.H2([
                "Fridge Details: ",
                html.Span(fridge_id, className="badge badge-blue")
            ]),
            dcc.Link("Back to Overview", href="/", style={
                'color': '#007bff', 'textDecoration': 'none', 'fontWeight': '600'
            })
        ], style={'marginBottom': '20px',
                  'display': 'flex',
                  'justifyContent': 'space-between',
                  'alignItems': 'center'}),

        # Hidden fridge_id
        html.Div(fridge_id, id='hidden-fridge-id', style={'display': 'none'}),

        # Poll interval
        dcc.Interval(id='detail-interval', interval=5000, n_intervals=0),

        # Graph container
        html.Div([
            html.H3("Temperature History"),
            dcc.Graph(id='temp-history-graph', figure={})
        ], id='graph-container', className='panel-box', style={'marginBottom': '20px'}),

        # Latest Readings
        html.Div([
            html.H3("Latest Readings"),
            html.Div(id='latest-readings', children=[])
        ], id='readings-container', className='panel-box', style={'marginBottom': '20px'}),

        # Control Section
        html.Div([
            html.H3("Set Temperature or Resistance"),

            html.Div([
                html.Label("Temp Channel:", style={'marginRight': '10px', 'fontWeight': '600'}),
                dcc.Input(
                    id='temp-channel-input',
                    type='text',
                    placeholder='e.g., A',
                    style={'padding': '6px', 'marginRight': '10px',
                           'borderRadius': '4px','border': '1px solid #ccc'}
                ),
                html.Label("Temp Value (K):", style={'marginRight': '10px','fontWeight':'600'}),
                dcc.Input(
                    id='temp-value-input',
                    type='text',
                    placeholder='e.g., 4.2',
                    style={'padding': '6px', 'marginRight': '10px',
                           'borderRadius':'4px','border':'1px solid #ccc'}
                ),
                html.Button("Set Temperature", id='set-temp-btn', n_clicks=0),
            ], style={'marginBottom': '15px','display':'flex','alignItems':'center'}),

            html.Div([
                html.Label("Resist Channel:", style={'marginRight': '10px','fontWeight':'600'}),
                dcc.Input(
                    id='resist-channel-input',
                    type='text',
                    placeholder='e.g., B',
                    style={'padding':'6px','marginRight':'10px',
                           'borderRadius':'4px','border':'1px solid #ccc'}
                ),
                html.Label("Resist Value (Ohms):", style={'marginRight': '10px','fontWeight':'600'}),
                dcc.Input(
                    id='resist-value-input',
                    type='text',
                    placeholder='e.g., 1000',
                    style={'padding':'6px','marginRight':'10px',
                           'borderRadius':'4px','border':'1px solid #ccc'}
                ),
                html.Button("Set Resistance", id='set-resist-btn', n_clicks=0),
            ], style={'marginBottom': '15px','display':'flex','alignItems':'center'}),

            html.Div(id='command-feedback', style={'marginTop': '15px'})
        ], id='control-section', className='panel-box')
    ], style={'padding': '20px'})
    return layout

def get_login_layout():
    layout = html.Div([
        html.H2("Please Log In", style={'marginTop': '10px', 'color': '#007bff'}),
        html.Div([
            html.Label("Username:", style={'marginBottom':'6px','fontWeight':'600'}),
            dcc.Input(id='login-username', type='text', placeholder='Username',
                      style={'display':'block','marginBottom':'15px','padding':'8px','width':'100%','borderRadius':'4px','border':'1px solid #ccc'}),

            html.Label("Password:", style={'marginBottom':'6px','fontWeight':'600'}),
            dcc.Input(id='login-password', type='password', placeholder='Password',
                      style={'display':'block','marginBottom':'20px','padding':'8px','width':'100%','borderRadius':'4px','border':'1px solid #ccc'}),

            html.Button("Login", id='login-button', n_clicks=0,
                style={'backgroundColor':'#28a745','color':'white','border':'none','padding':'10px 15px','borderRadius':'4px','cursor':'pointer','width':'100%','fontWeight':'600'}),

            html.Div(id='login-error-msg', style={'marginTop':'10px'}),
            html.Div([
                dcc.Link("Back to Overview", href="/", style={'color':'#007bff','textDecoration':'none'})
            ], style={'marginTop':'20px','textAlign':'center'})
        ], style={
            'maxWidth':'400px','margin':'0 auto','padding':'30px','borderRadius':'8px',
            'boxShadow':'0 4px 6px rgba(0,0,0,0.1)'
        })
    ], style={'padding': '20px'})
    return layout
