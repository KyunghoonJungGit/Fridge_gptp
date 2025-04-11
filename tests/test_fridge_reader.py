""" 
@description
Tests for backend.data_acquisition.fridge_reader.

Key features:
- Verifies that the DummyBlueforsSlave instances initialize correctly.
- Checks the functionality of get_fridge_ids(), get_fridge_instance(), get_current_data(), and poll_all_fridges().
- Ensures the module handles unknown fridge IDs gracefully.

@dependencies
- pytest: testing framework
- backend.data_acquisition.fridge_reader
- We rely on the dummy_bluefors_fridge simulator for actual fridge behavior.

@notes
- Tests use the actual dummy classes (no mocks). 
- For more advanced scenarios, consider mocking or patching time-based functions.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.data_acquisition import fridge_reader

def test_init_fridges():
    """
    Test that init_fridges() successfully creates and stores multiple DummyBlueforsSlave objects.
    """
    # Make sure we re-initialize for this test (in case global state changed).
    fridge_reader.init_fridges()
    ids = fridge_reader.get_fridge_ids()
    
    assert len(ids) >= 2, "Expected at least two fridges to be initialized"
    assert "fridge_1" in ids, "Fridge 'fridge_1' should be initialized"
    assert "fridge_2" in ids, "Fridge 'fridge_2' should be initialized"

def test_get_fridge_instance_valid():
    """
    Test that get_fridge_instance returns a DummyBlueforsSlave object for a known fridge_id.
    """
    fridge_reader.init_fridges()
    fridge_obj = fridge_reader.get_fridge_instance("fridge_1")
    assert fridge_obj is not None, "Should return a valid DummyBlueforsSlave object"

def test_get_fridge_instance_invalid():
    """
    Test that get_fridge_instance raises KeyError for an unknown fridge_id.
    """
    fridge_reader.init_fridges()
    with pytest.raises(KeyError):
        fridge_reader.get_fridge_instance("unknown_fridge_id")

def test_get_current_data():
    """
    Test get_current_data returns a dictionary with expected fields.
    """
    fridge_reader.init_fridges()
    data = fridge_reader.get_current_data("fridge_1")
    assert isinstance(data, dict), "Expected a dictionary of data"
    assert "fridge_id" in data, "Data should include fridge_id"
    assert "channels" in data, "Data should include channels sub-dict"
    assert "sensor_status" in data, "Data should include sensor_status"
    assert "last_pressures_mbar" in data, "Data should include last_pressures_mbar"
    assert data["fridge_id"] == "fridge_1", "Returned fridge_id should match requested ID"

def test_poll_all_fridges():
    """
    Test poll_all_fridges updates the in-memory cache for each known fridge 
    and doesn't raise exceptions.
    """
    fridge_reader.init_fridges()
    
    # Initially, the cache might be empty
    # We'll call poll_all_fridges and ensure it doesn't fail
    fridge_reader.poll_all_fridges()
    
    for fid in fridge_reader.get_fridge_ids():
        latest = fridge_reader.get_latest_data(fid)
        assert isinstance(latest, dict), f"Expected dictionary for fridge {fid}"
        assert latest.get("fridge_id") == fid, f"Latest data should match fridge_id {fid}"