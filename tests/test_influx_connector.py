"""
@description
Tests for backend.db.influx_connector.

Key features:
- Ensures the init_influxdb_client() function doesn't crash.
- Tests write_data() in a minimal scenario, possibly with a mock or by skipping if InfluxDB is not available.
- (Optional) Tests query_data() with a mock or an actual local Influx instance.

@dependencies
- pytest
- backend.db.influx_connector
- We rely on environment variables for InfluxDB credentials. 
- In a real environment, consider mocking or setting up a local InfluxDB in test mode.

@notes
- Because we may not have a real InfluxDB server running, these tests might be partial or skipped.
- If an InfluxDB instance is not running, write_data might fail or log warnings. 
- For demonstration, we catch exceptions and verify no crashes.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.db import influx_connector

def test_init_influxdb_client():
    """
    Test that init_influxdb_client() can be called without raising exceptions.
    """
    try:
        influx_connector.init_influxdb_client()
    except Exception as ex:
        pytest.fail(f"init_influxdb_client() raised an exception: {ex}")

def test_write_data_no_crash():
    """
    Test that write_data() doesn't crash even if InfluxDB is unavailable.
    This is a minimal test; in real usage, we would mock the InfluxDBClient.
    """
    # We'll just ensure it logs a warning or passes gracefully.
    try:
        influx_connector.write_data("test_measurement", {"fridge_id": "test_fridge", "test_field": 123})
    except Exception as ex:
        pytest.fail(f"write_data() raised an exception unexpectedly: {ex}")

@pytest.mark.skip(reason="Requires a running InfluxDB to validate query results")
def test_query_data():
    """
    Example test that queries data from InfluxDB.
    Skipped by default because it requires a live InfluxDB.

    In a real test environment, set up a local test container and remove the skip.
    """
    try:
        results = influx_connector.query_data('from(bucket:"my-bucket") |> range(start: -1h)')
        # We can't assert much without real data, so just assert it's a list
        assert isinstance(results, list), "Expected a list of query results"
    except Exception as ex:
        pytest.fail(f"query_data() raised an exception unexpectedly: {ex}")
