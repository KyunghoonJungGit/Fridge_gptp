"""
@description
Manages multiple DummyBlueforsSlave instances (one per fridge). Provides functions 
to initialize, retrieve, and query data from these dummy fridge objects.

Key features:
- init_fridges(): create and store multiple DummyBlueforsSlave objects in an internal dictionary.
- get_fridge_ids(): retrieve a list of all fridge IDs managed by this module.
- get_fridge_instance(fridge_id): fetch a reference to the specified DummyBlueforsSlave instance.
- get_current_data(fridge_id): return a current snapshot (dict) of sensor/state data from a given fridge.

@dependencies
- Python standard libraries: typing, datetime
- Project modules: dummpy_bluefors_fridge (DummyBlueforsSlave), backend.utils.logger (for logging)
  
@notes
- This is a foundational step. Additional logic (e.g., polling or scheduling) will be introduced in later steps.
- The plan suggests we might store these readings in InfluxDB in a future step, but that is not handled here.
"""

from typing import Dict, Any, List
from datetime import datetime

# We import our DummyBlueforsSlave from the existing dummpy_bluefors_fridge.py
# (Note the unusual file name 'dummpy' in the repository.)
from dummpy_bluefors_fridge import DummyBlueforsSlave

# We also import our logging utility for consistent log messages
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Internal dictionary mapping fridge_id -> DummyBlueforsSlave instance
_fridges: Dict[str, DummyBlueforsSlave] = {}


def init_fridges() -> None:
    """
    Create and store multiple DummyBlueforsSlave objects in the _fridges dictionary.
    
    :return: None
    """
    logger.info("Initializing dummy fridges...")

    # Example: define 2 dummy fridge instances for demonstration
    # You can adjust the number and naming as appropriate.
    # Each instance typically requires a nickname, password, address, port, logs_path (optional)
    fridge_1 = DummyBlueforsSlave(
        nickname="fridge_1_nickname",
        password="dummy_pass",
        server_address="127.0.0.1",
        server_port=9001,
        logs_path=None  # No file logging, keep everything in memory
    )

    fridge_2 = DummyBlueforsSlave(
        nickname="fridge_2_nickname",
        password="dummy_pass",
        server_address="127.0.0.1",
        server_port=9002,
        logs_path=None
    )

    # Store them with unique fridge IDs
    _fridges["fridge_1"] = fridge_1
    _fridges["fridge_2"] = fridge_2

    logger.info("Dummy fridges initialized: %s", list(_fridges.keys()))


def get_fridge_ids() -> List[str]:
    """
    Return a list of all known fridge IDs (keys of the _fridges dictionary).
    
    :return: A list of fridge IDs.
    """
    return list(_fridges.keys())


def get_fridge_instance(fridge_id: str) -> DummyBlueforsSlave:
    """
    Retrieve the DummyBlueforsSlave instance for a given fridge ID.
    
    :param fridge_id: The unique ID of the fridge.
    :return: The associated DummyBlueforsSlave instance.
    :raises KeyError: If the fridge_id is not found.
    """
    if fridge_id not in _fridges:
        logger.error("Fridge ID '%s' not found in _fridges.", fridge_id)
        raise KeyError(f"Unknown fridge_id '{fridge_id}'.")
    return _fridges[fridge_id]


def get_current_data(fridge_id: str) -> Dict[str, Any]:
    """
    Return a simple dictionary of current data (temperatures, states, etc.) from the specified fridge.
    
    :param fridge_id: The unique ID of the fridge to query.
    :return: A dictionary with relevant information about the fridge's current state and sensor readings.
    :raises KeyError: If the fridge_id is not found in _fridges.
    """
    fridge = get_fridge_instance(fridge_id)

    # For demonstration, we'll compile a small snapshot of current data.
    # Feel free to add or remove keys as needed.
    state_dict = fridge.dict_state(0)  # full channel states
    status_row = fridge.get_status()   # [date, time, sensor1, value1, sensor2, value2, ...]
    pressures = fridge.get_last_pressures() or []

    # Convert the status_row into a dict for clarity
    # status_row format: [date, time, sensorKey1, val1, sensorKey2, val2, ...]
    status_dict = {}
    if status_row and len(status_row) > 2:
        # Skip the first two entries (date, time), then parse sensorKey/val pairs
        for idx in range(2, len(status_row), 2):
            sensor_key = status_row[idx]
            sensor_val = status_row[idx + 1]
            status_dict[sensor_key] = sensor_val

    # Build a structured return object
    data_snapshot = {
        "fridge_id": fridge_id,
        "timestamp": datetime.now().isoformat(),
        "channels": {
            k: v for k, v in state_dict.items() if k != "datetime"
        },
        "sensor_status": status_dict,
        "last_pressures_mbar": pressures,
        "state_message": fridge.generate_state_message()
    }

    return data_snapshot
