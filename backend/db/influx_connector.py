"""
@description
Handles writing and reading data to/from InfluxDB. 
Provides a simple interface to:
 - Initialize an InfluxDB client using credentials from the .env file
 - Write sensor data (or event logs) to a specified measurement
 - Query historical data using InfluxQL or the Flux query language

Key features:
- write_data(measurement_name, data_dict): writes sensor values to InfluxDB
- query_data(query_string): runs a Flux query and returns the parsed results

@dependencies
- influxdb-client: The official InfluxDB Python client library
- python-dotenv (.env): environment variables for InfluxDB connection details
- backend.utils.logger: for consistent logging

@notes
- This module expects the following environment variables:
    INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
- If any variable is missing, defaults are used (e.g., localhost, etc.)
- For local dev, ensure you have a running InfluxDB instance or Docker container
"""

import os
import logging
from typing import Any, Dict, List

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# We reuse our project-wide logger
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Global references to InfluxDB client, org, and bucket
_influx_client = None
_influx_org = None
_influx_bucket = None

def init_influxdb_client() -> None:
    """
    Initialize the global InfluxDB client using environment variables.
    This is called once (ideally at server startup).
    """
    global _influx_client, _influx_org, _influx_bucket

    if _influx_client is not None:
        # Already initialized
        return

    # Read environment variables from .env or system environment
    url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    token = os.getenv("INFLUXDB_TOKEN", "my-super-secret-token")
    _influx_org = os.getenv("INFLUXDB_ORG", "my-org")
    _influx_bucket = os.getenv("INFLUXDB_BUCKET", "my-bucket")

    logger.info("[influx_connector] Initializing InfluxDBClient with:")
    logger.info(" -> URL: %s, Org: %s, Bucket: %s", url, _influx_org, _influx_bucket)

    try:
        _influx_client = InfluxDBClient(url=url, token=token, org=_influx_org)
        logger.info("[influx_connector] InfluxDB client initialized successfully.")
    except Exception as e:
        logger.error("[influx_connector] Error initializing InfluxDB client: %s", e)
        _influx_client = None

def write_data(measurement_name: str, data_dict: Dict[str, Any]) -> None:
    """
    Write a single data point to the specified measurement in InfluxDB.

    :param measurement_name: The name of the measurement (e.g., "temperature_readings").
    :param data_dict: A dictionary of field values. Example:
        {
            "fridge_id": "fridge_1",
            "temperature": 1.4,
            "pressure": 0.0002,
            "status": "Normal"
        }
    :return: None
    """
    global _influx_client, _influx_bucket, _influx_org
    if not _influx_client:
        logger.warning("[influx_connector] Attempting to write data but InfluxDB client is not initialized.")
        return

    try:
        # Construct the data point
        point = Point(measurement_name)
        # By convention, we store fridge_id (if present) as a tag
        # All other numeric/string values go as fields
        # (You can adapt this logic to your specific needs)
        fridge_id = data_dict.get("fridge_id")
        if fridge_id:
            point = point.tag("fridge_id", fridge_id)

        # Add fields
        # We skip 'fridge_id' if it's already used as a tag
        for k, v in data_dict.items():
            if k == "fridge_id":
                continue
            point = point.field(k, v)

        # Write to InfluxDB
        with _influx_client.write_api(write_options=SYNCHRONOUS) as write_api:
            write_api.write(bucket=_influx_bucket, org=_influx_org, record=point)
        logger.info("[influx_connector] Wrote data to '%s' measurement: %s", measurement_name, data_dict)

    except Exception as e:
        logger.error("[influx_connector] Error writing data to InfluxDB: %s", e)

def query_data(query_string: str) -> List[Dict[str, Any]]:
    """
    Execute a Flux query and return the results as a list of dictionaries.

    :param query_string: The Flux query to be executed against the InfluxDB instance.
    :return: A list of dictionaries representing rows in the result set.
    """
    global _influx_client
    results_list = []

    if not _influx_client:
        logger.warning("[influx_connector] Attempting to query data but InfluxDB client is not initialized.")
        return results_list

    try:
        query_api = _influx_client.query_api()
        tables = query_api.query(query_string)

        for table in tables:
            for record in table.records:
                # Convert record values to a dictionary
                row = {
                    "measurement": record.measurement,
                    "time": record.get_time(),
                }
                # record.values holds all fields and tags
                # We'll merge them into the row dictionary
                row.update(record.values)
                results_list.append(row)

    except Exception as e:
        logger.error("[influx_connector] Error querying data from InfluxDB: %s", e)

    return results_list

def close_influxdb_client() -> None:
    """
    Close the global InfluxDB client.
    This can be invoked on server shutdown if desired.
    """
    global _influx_client
    if _influx_client:
        _influx_client.close()
        logger.info("[influx_connector] InfluxDB client closed.")
        _influx_client = None
