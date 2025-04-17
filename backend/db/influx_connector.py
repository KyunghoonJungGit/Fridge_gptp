"""
@description
Handles writing and reading data to/from InfluxDB. 
Provides a simple interface to:
 - Initialize an InfluxDB client using credentials from the .env file
 - Write sensor data (or event logs) to a specified measurement
 - Query historical data using InfluxQL or the Flux query language

Key features:
- init_influxdb_client(): sets up a global InfluxDBClient with org, bucket
- write_data(): writes a single data point
- query_data(): runs a Flux query and returns the results as a list of dicts
- close_influxdb_client(): closes the global client
- get_influx_bucket(): returns the name of the current bucket (so the UI can query it)

@dependencies
- influxdb-client: The official InfluxDB Python client library
- python-dotenv for environment variables

@notes
- If the user-specified bucket does not exist, we create it automatically.
- The environment variables:
    INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
  can override default connection settings.
"""

import os
from typing import Any, Dict, List

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from backend.utils.logger import get_logger

logger = get_logger(__name__)

_influx_client = None
_influx_org = None
_influx_bucket = None

def init_influxdb_client() -> None:
    """
    Initialize the global InfluxDB client using environment variables.
    If the configured bucket doesn't exist, create it automatically.
    """
    global _influx_client, _influx_org, _influx_bucket

    if _influx_client is not None:
        # Already initialized
        return

    # Read environment variables
    url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    token = os.getenv("INFLUXDB_TOKEN", "my-super-secret-token")
    _influx_org = os.getenv("INFLUXDB_ORG", "my-org")
    _influx_bucket = os.getenv("INFLUXDB_BUCKET", "my-bucket")

    logger.info("[influx_connector] Initializing InfluxDBClient with:")
    logger.info(" -> URL: %s, Org: %s, Bucket: %s", url, _influx_org, _influx_bucket)

    try:
        _influx_client = InfluxDBClient(url=url, token=token, org=_influx_org)
        logger.info("[influx_connector] InfluxDB client initialized successfully.")

        # Attempt to create the bucket if it doesn't exist
        buckets_api = _influx_client.buckets_api()
        existing_buckets = buckets_api.find_buckets().buckets
        if not any(b.name == _influx_bucket for b in existing_buckets):
            buckets_api.create_bucket(bucket_name=_influx_bucket, org=_influx_org)
            logger.info("[influx_connector] Created bucket '%s' because it did not exist.", _influx_bucket)

    except Exception as e:
        logger.error("[influx_connector] Error initializing InfluxDB client: %s", e)
        _influx_client = None

def get_influx_bucket() -> str:
    """
    Return the name of the currently configured InfluxDB bucket.
    Useful for queries in other parts of the code.
    """
    global _influx_bucket
    return _influx_bucket or "my-bucket"

def write_data(measurement_name: str, data_dict: Dict[str, Any]) -> None:
    """
    Write a single data point to the specified measurement in InfluxDB.

    :param measurement_name: The measurement name (e.g. "temperature_readings").
    :param data_dict: Fields/tags. For example:
        {
            "fridge_id": "fridge_1",
            "temperature": 1.4,
            "pressure": 0.0002,
            "status": "Normal"
        }
    """
    global _influx_client, _influx_bucket, _influx_org
    if not _influx_client:
        logger.warning("[influx_connector] Attempting to write data but InfluxDB client is not initialized.")
        return

    try:
        point = Point(measurement_name)
        fridge_id = data_dict.get("fridge_id")
        if fridge_id:
            point = point.tag("fridge_id", fridge_id)

        for k, v in data_dict.items():
            if k == "fridge_id":
                continue
            point = point.field(k, v)

        with _influx_client.write_api(write_options=SYNCHRONOUS) as write_api:
            write_api.write(bucket=_influx_bucket, org=_influx_org, record=point)
        logger.info("[influx_connector] Wrote data to '%s' measurement: %s", measurement_name, data_dict)

    except Exception as e:
        logger.error("[influx_connector] Error writing data to InfluxDB: %s", e)

def query_data(query_string: str) -> List[Dict[str, Any]]:
    """
    Execute a Flux query and return the results as a list of dictionaries.

    :param query_string: The Flux query to be executed.
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
                row = {
                    "measurement": record.measurement,
                    "time": record.get_time()
                }
                row.update(record.values)
                results_list.append(row)

    except Exception as e:
        logger.error("[influx_connector] Error querying data from InfluxDB: %s", e)

    return results_list

def close_influxdb_client() -> None:
    """
    Close the global InfluxDB client (e.g. on server shutdown).
    """
    global _influx_client
    if _influx_client:
        _influx_client.close()
        logger.info("[influx_connector] InfluxDB client closed.")
        _influx_client = None
