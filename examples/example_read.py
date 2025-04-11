"""
@description
An example script demonstrating how to read fridge data from the remote server
using the python_client FridgeClient class.

Key features:
1. Shows basic usage: create FridgeClient, call get_latest_data
2. Logs or prints out the results

@dependencies
- The local python_client package (installed via 'pip install .')
- A running fridge monitoring server (http://localhost:8050 or another URL)
- Python 3.x

@notes
- If needed, adapt to handle exceptions or print more detailed output.
"""

import sys
from python_client.client import FridgeClient

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8050"

    client = FridgeClient(base_url)
    try:
        data = client.get_latest_data("fridge_1")
        print("Latest data for fridge_1:\n", data)
    except Exception as e:
        print("Error occurred:", e)

if __name__ == "__main__":
    main()
