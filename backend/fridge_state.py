""" 
@description
Maintains the fridge state and polling logic for the real fridge system, 
decoupled from app.py to avoid circular imports.

Key features:
- get_fridge_ids(): returns a list of known fridge IDs
- get_latest_data(fridge_id): returns the polled data
- poll_all_fridges(): updates the polled data in memory
- pop_all_alerts(): retrieves and clears accumulated alerts

@dependencies
- backend.fridge_api.real_fridge for the RealFridge calls
- Python standard libraries for data structures
- Logging if needed
@notes
- This is a typical 'service' or 'state' module with no Dash or Flask imports
"""

from typing import Dict, Any
import logging
from backend.fridge_api.real_fridge import RealFridge

logger = logging.getLogger(__name__)

# We'll track all known fridges in a list:
AVAILABLE_FRIDGES = ["fridge_1", "fridge_2"]

# We keep polled data in memory
_latest_data: Dict[str, Dict[str, Any]] = {}
# Alerts in memory
_latest_alerts: Dict[str, list] = {}

def get_fridge_ids() -> list:
    """Return a list of the available fridge IDs."""
    return AVAILABLE_FRIDGES

def get_latest_data(fridge_id: str) -> dict:
    """Retrieve the last polled data for the given fridge, or an empty dict if none."""
    return _latest_data.get(fridge_id, {})

def poll_all_fridges() -> None:
    """Poll each fridge for current data and store it in _latest_data."""
    for fid in AVAILABLE_FRIDGES:
        try:
            fridge = RealFridge(fid)
            data = fridge.get_current_data()
            _latest_data[fid] = data
        except Exception as e:
            logger.error(f"Error polling fridge {fid}: {e}")

def pop_all_alerts() -> dict:
    """
    Return and clear all accumulated alerts for all fridges.
    If you only want per fridge, adapt accordingly.
    """
    alerts_copy = dict(_latest_alerts)
    _latest_alerts.clear()
    return alerts_copy
