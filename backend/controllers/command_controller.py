""" 
@description
Defines a command controller that accepts fridge ID, command name, and parameters,
then invokes the corresponding methods on the DummyBlueforsSlave instance.

Key features:
- Accept a command string (e.g. "toggle_compressor", "set_channel") and optional params
- Find the correct fridge instance and call the associated method
- Log command execution to InfluxDB for auditing

@dependencies
- backend.data_acquisition.fridge_reader (to get DummyBlueforsSlave instances)
- backend.db.influx_connector (for optional command logging)
- backend.utils.logger (shared logger)

@notes
- If the command is unknown or if required params are missing, we log an error and return False
- For "set_channel", we expect `params` to contain "channel" and "value"
- For "toggle_valve" or "toggle_heat_switch", we expect `params` to contain the valve or switch name
"""

from datetime import datetime
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger
from backend.data_acquisition.fridge_reader import get_fridge_instance
from backend.db.influx_connector import write_data

logger = get_logger(__name__)

def execute_command(fridge_id: str, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Execute a specified command on the given fridge.

    :param fridge_id: The unique ID of the fridge (e.g. 'fridge_1')
    :param command: The command to execute (e.g., "toggle_compressor", "toggle_valve")
    :param params: Optional dictionary of extra parameters (e.g., {"valve_name": "v5"})
    :return: True if command executed successfully, otherwise False.
    :raises KeyError or ValueError: If the fridge_id is invalid or the command is malformed.
    """
    if params is None:
        params = {}

    # Retrieve the fridge instance
    try:
        fridge = get_fridge_instance(fridge_id)
    except KeyError as e:
        logger.error("[command_controller] Unknown fridge_id='%s': %s", fridge_id, e)
        return False

    # Command routing
    command = command.strip().lower()
    success = False

    try:
        if command == "toggle_compressor":
            fridge.toggle_compressor()
            success = True

        elif command == "toggle_pulsetube":
            fridge.toggle_pulsetube()
            success = True

        elif command == "toggle_turbo":
            fridge.toggle_turbo()
            success = True

        elif command == "toggle_valve":
            valve_name = params.get("valve_name")
            if not valve_name:
                logger.error("[command_controller] Missing 'valve_name' param for toggle_valve.")
            else:
                fridge.toggle_valve(valve_name)
                success = True

        elif command == "toggle_heat_switch":
            hs_name = params.get("heat_switch_name")
            if not hs_name:
                logger.error("[command_controller] Missing 'heat_switch_name' param for toggle_heat_switch.")
            else:
                fridge.toggle_heat_switch(hs_name)
                success = True

        elif command == "set_channel":
            ch_name = params.get("channel")
            val = params.get("value")
            if (ch_name is None) or (val is None):
                logger.error("[command_controller] Missing 'channel' or 'value' param for set_channel.")
            else:
                fridge.set_channel(ch_name, val)
                success = True

        else:
            logger.error("[command_controller] Unknown command='%s'.", command)

    except Exception as ex:
        logger.exception("[command_controller] Error executing command='%s': %s", command, ex)
        success = False

    # If success, optionally log the command to InfluxDB
    if success:
        _log_command_to_influx(fridge_id, command, params)

    return success

def _log_command_to_influx(fridge_id: str, command: str, params: Dict[str, Any]) -> None:
    """
    Internal helper to log command execution in InfluxDB for auditing.

    :param fridge_id: The fridge on which the command was executed
    :param command: The command name
    :param params: Dictionary of any additional parameters
    :return: None
    """
    # Prepare a data dict for the "command_log" measurement
    data = {
        "fridge_id": fridge_id,
        "command": command,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Flatten params into fields (with string representation)
    for k, v in params.items():
        data[k] = str(v)

    # Attempt to write to InfluxDB
    try:
        write_data("command_log", data)
    except Exception as e:
        logger.error("[command_controller] Failed to log command to InfluxDB: %s", e)
