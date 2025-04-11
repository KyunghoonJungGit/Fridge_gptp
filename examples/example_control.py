"""
@description
Example script showing how to send commands to a remote fridge using the python_client FridgeClient.

Key features:
1. Toggles a valve (v5) on fridge_1
2. Checks if the command was successful
3. Optionally toggles the pulsetube

@dependencies
- The local python_client package
- A running fridge monitoring server

@notes
- In a real scenario, error handling and validations would be more robust.
- Example usage:
  python example_control.py [base_url]
"""

import sys
from python_client.client import FridgeClient

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8050"

    client = FridgeClient(base_url)

    # Toggle valve v5
    success = client.send_command("fridge_1", "toggle_valve", {"valve_name": "v5"})
    if success:
        print("Successfully toggled valve 'v5'")
    else:
        print("Failed to toggle valve 'v5'")

    # Optionally toggle the pulsetube
    success_pt = client.send_command("fridge_1", "toggle_pulsetube")
    if success_pt:
        print("Pulsetube toggled successfully!")
    else:
        print("Pulsetube toggle failed.")

if __name__ == "__main__":
    main()
