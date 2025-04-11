"""
@description
Tests for backend.controllers.command_controller.

Key features:
- Validates the execute_command() functionality with known commands and parameters.
- Checks handling of invalid fridge IDs, unknown commands, missing params, etc.
- Verifies success/failure return values.

@dependencies
- pytest: testing framework
- backend.controllers.command_controller
- backend.data_acquisition.fridge_reader to initialize fridges
- The dummy fridge simulator for actual state changes.

@notes
- We call init_fridges() before tests to ensure a stable environment.
- The tests directly observe return values from execute_command().
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.controllers import command_controller
from backend.data_acquisition import fridge_reader

def setup_module(module):
    """
    Setup function (runs once per module) to initialize dummy fridges.
    """
    fridge_reader.init_fridges()

def test_execute_command_valid_toggle_pulsetube():
    """
    Test toggling the pulsetube on a valid fridge ID.
    """
    result = command_controller.execute_command("fridge_1", "toggle_pulsetube")
    assert result is True, "Expected toggling pulsetube to succeed"

def test_execute_command_invalid_fridge_id():
    """
    Test passing an invalid fridge ID raises an error log and returns False.
    """
    result = command_controller.execute_command("invalid_id", "toggle_pulsetube")
    assert result is False, "Should return False for unknown fridge_id"

def test_execute_command_unknown_command():
    """
    Test that an unrecognized command returns False.
    """
    result = command_controller.execute_command("fridge_1", "unknown_command")
    assert result is False, "Unknown command should return False"

def test_execute_command_toggle_valve_missing_param():
    """
    Test toggle_valve fails if valve_name is missing in params.
    """
    # Missing 'valve_name' in params
    result = command_controller.execute_command("fridge_1", "toggle_valve", {})
    assert result is False, "Should fail if required param is missing"

def test_execute_command_toggle_valve_valid():
    """
    Test a valid valve toggle command.
    """
    result = command_controller.execute_command("fridge_1", "toggle_valve", {"valve_name": "v5"})
    assert result is True, "Toggling a known valve should succeed"
