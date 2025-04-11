"""
@description
A Python client that interacts with the Fridge Monitoring system's REST-like API endpoints.

Key features:
1. FridgeClient class with:
   - get_latest_data(fridge_id): fetch JSON from /api/fridge/<fridge_id>/latest
   - send_command(fridge_id, command, params): POST to /api/fridge/<fridge_id>/command
   - get_fridge_ids(): optional function to glean known fridge IDs if exposed by the server (not implemented here).
2. Uses the requests library to communicate with the Dash/Flask server.

@dependencies
- requests library
- The server must be running and accessible at the base_url provided.

@notes
- This is a minimal example. In a real environment, you might handle authentication tokens or session cookies.
- If the server enforces login, we would need a /login API route to obtain a cookie or token.
"""

import requests
from typing import Dict, Any, Optional

class FridgeClient:
    """
    A simple client for remote fridge monitoring and control.

    Example usage:
    ```
    client = FridgeClient("http://localhost:8050")
    data = client.get_latest_data("fridge_1")
    print("Latest data:", data)
    result = client.send_command("fridge_1", "toggle_pulsetube")
    print("Command success?", result)
    ```
    """

    def __init__(self, base_url: str):
        """
        :param base_url: The base URL of the fridge monitoring server, e.g. "http://localhost:8050"
        """
        self.base_url = base_url.rstrip("/")

    def get_latest_data(self, fridge_id: str) -> Dict[str, Any]:
        """
        Retrieve the latest polled data for the specified fridge.

        :param fridge_id: The unique fridge ID (e.g. 'fridge_1')
        :return: A dictionary of fridge data, or raises an exception if unsuccessful.
        """
        url = f"{self.base_url}/api/fridge/{fridge_id}/latest"
        response = requests.get(url)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to get latest data (status={response.status_code}). {response.text}")
        resp_json = response.json()
        if not resp_json.get("success"):
            err_msg = resp_json.get("error", "Unknown error")
            raise RuntimeError(f"API responded with success=false: {err_msg}")
        return resp_json.get("data", {})

    def send_command(self, fridge_id: str, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a command to the specified fridge.

        :param fridge_id: The unique fridge ID
        :param command: The command string (e.g. 'toggle_valve', 'toggle_pulsetube')
        :param params: Optional dictionary of parameters (e.g. {"valve_name": "v5"})
        :return: True if command was executed successfully, False otherwise.
        """
        if params is None:
            params = {}
        url = f"{self.base_url}/api/fridge/{fridge_id}/command"
        payload = {
            "command": command,
            "params": params
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200 and response.status_code != 400:
            # Could be 500 or something else
            raise RuntimeError(f"Command request failed (status={response.status_code}). {response.text}")
        resp_json = response.json()
        return bool(resp_json.get("success", False))
