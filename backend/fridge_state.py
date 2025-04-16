""" @description
Maintains the fridge state and polling logic for the real fridge system, 
decoupled from app.py to avoid circular imports.

Key features:
- get_fridge_ids(): returns a list of known fridge IDs
- get_latest_data(fridge_id): returns the polled data
- poll_all_fridges(): updates the polled data in memory AND logs it to InfluxDB
- pop_all_alerts(): retrieves and clears accumulated alerts

@dependencies
- backend.fridge_api.real_fridge for the RealFridge calls
- backend.db.influx_connector.write_data for logging
- Python standard libraries for data structures
- Logging if needed

@notes
- We add a call to 'write_data' after successfully polling each fridge
"""

from typing import Dict, Any
import logging

from backend.fridge_api.real_fridge import RealFridge
# We add the InfluxDB logging call:
from backend.db.influx_connector import write_data

logger = logging.getLogger(__name__)

# We'll track all known fridges in a list:
AVAILABLE_FRIDGES = ["fridge_1", "fridge_2"]

# We keep polled data in memory
_latest_data: Dict[str, Dict[str, Any]] = {}
# Alerts in memory
_latest_alerts: Dict[str, list] = {}

def get_fridge_ids() -> list:
    """
    Return a list of the available fridge IDs (e.g. fridge_1, fridge_2).
    """
    return AVAILABLE_FRIDGES

def get_latest_data(fridge_id: str) -> dict:
    """
    Retrieve the last polled data for the given fridge, or an empty dict if none.
    :param fridge_id: ID of the fridge
    :return: A dict with the polled data, e.g. { 'fridge_id':..., 'sensor_status':..., ... }
    """
    return _latest_data.get(fridge_id, {})

def poll_all_fridges() -> None:
    """
    Poll each fridge for current data and store it in _latest_data.
    Also logs temperature & pressure to InfluxDB under measurement 'fridge_data'.
    """
    for fid in AVAILABLE_FRIDGES:
        try:
            fridge = RealFridge(fid)
            data = fridge.get_current_data()
            _latest_data[fid] = data

            # Try to log some basics to InfluxDB
            # We'll record fridge_id, channel A/B temps & presses, and a timestamp
            if "channels" in data:
                chA = data["channels"].get("A", {})
                chB = data["channels"].get("B", {})

                influx_body = {
                    "fridge_id": fid,
                    "temp_chA": chA.get("temp", None),
                    "pres_chA": chA.get("pres", None),
                    "temp_chB": chB.get("temp", None),
                    "pres_chB": chB.get("pres", None),
                    "timestamp": data.get("timestamp", "")
                }
                write_data("fridge_data", influx_body)
            
        except Exception as e:
            logger.error(f"Error polling fridge {fid}: {e}")

def pop_all_alerts() -> dict:
    """
    Return and clear all accumulated alerts for all fridges.
    If you only want per fridge, adapt accordingly.
    :return: dict of { fridge_id: [list_of_alerts], ... }
    """
    alerts_copy = dict(_latest_alerts)
    _latest_alerts.clear()
    return alerts_copy
