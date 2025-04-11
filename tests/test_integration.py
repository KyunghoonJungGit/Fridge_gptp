"""
@description
Optional integration test that attempts to start the Dash app and access a simple endpoint.

Key features:
- Uses the 'requests' library to call the local server.
- Confirms the main page returns HTTP 200.
- Demonstrates how to test end-to-end, though this is limited and minimal.

@dependencies
- pytest
- requests
- threading or subprocess to start the Dash server
- time: to allow the server to start

@notes
- This test starts the app in a background thread or process, then queries it.
- For a real CI environment, you'd manage the server more robustly.
"""

import pytest
import threading
import time
import sys
from pathlib import Path

# Add the project root to Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import requests conditionally
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from backend.app import app

@pytest.mark.skip(reason="Optional integration test. Enable if you want to spin up a local server.")
def test_dash_app_running():
    """
    Starts the Dash app in a background thread and checks the main page is accessible.
    Requires the 'requests' package to be installed.
    """
    # Skip this test if requests is not available
    if not REQUESTS_AVAILABLE:
        pytest.skip("'requests' package is not installed. Run 'pip install requests' to enable this test.")
        
    def run_app():
        app.run_server(debug=False, host="127.0.0.1", port=8050)

    # Start the server in a background thread
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()

    # Allow some time for the server to start
    time.sleep(2)

    # Make a request to the main page
    response = requests.get("http://127.0.0.1:8050/")
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
