""" 
@description
Defines a command controller that accepts fridge ID, command name, and parameters,
then invokes the corresponding methods on the RealFridge instance.

Key features:
- Accept a command string (e.g. "set_temp", "set_resist") and optional params
- Instantiate RealFridge(fridge_id) and call the associated method
- Log command execution to InfluxDB for auditing (if desired)

@dependencies
- backend.fridge_api.real_fridge (to get RealFridge instances)
- backend.db.influx_connector (for optional command logging)
- backend.utils.logger (shared logger)

@notes
- We no longer handle old toggle commands like "toggle_valve" or "toggle_compressor."
- For "set_temp", we expect `params` to contain "channel" (e.g. "A") and "value" (the setpoint)
- For "set_resist", we expect `params` to contain "channel" and "value"
"""

from datetime import datetime
from typing import Any, Dict, Optional

from backend.utils.logger import get_logger
from backend.db.influx_connector import write_data
from backend.fridge_api.real_fridge import RealFridge

logger = get_logger(__name__)

def execute_command(fridge_id: str, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
    """
    Execute a specified command on the given fridge via the RealFridge API.

    :param fridge_id: The unique ID of the fridge (e.g. 'fridge_1')
    :param command: The command to execute (e.g., "set_temp", "set_resist")
    :param params: Optional dictionary of extra parameters (e.g., {"channel": "A", "value": 4.2})
    :return: True if command executed successfully, otherwise False.
    :raises KeyError or ValueError: If missing expected params or unknown command.
    """
    if params is None:
        params = {}

    # Instantiate the real fridge wrapper
    fridge = RealFridge(fridge_id)

    # Sanitize command
    cmd_lower = command.strip().lower()
    success = False

    try:
        if cmd_lower == "set_temp":
            # Expect 'channel' and 'value' in params
            ch_name = params.get("channel")
            val = params.get("value")
            if ch_name is None or val is None:
                logger.error("[command_controller] Missing 'channel' or 'value' param for set_temp.")
            else:
                # Convert val to float if needed
                float_val = float(val)
                fridge.set_temp(ch_name, float_val)
                success = True

        elif cmd_lower == "set_resist":
            ch_name = params.get("channel")
            val = params.get("value")
            if ch_name is None or val is None:
                logger.error("[command_controller] Missing 'channel' or 'value' param for set_resist.")
            else:
                float_val = float(val)
                fridge.set_resist(ch_name, float_val)
                success = True

        else:
            logger.error("[command_controller] Unknown command='%s'.", cmd_lower)

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
