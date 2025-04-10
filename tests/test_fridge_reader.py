"""
Test script for fridge_reader.py functionality
"""
import sys
from pathlib import Path
import unittest

# Add the project root to Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.data_acquisition.fridge_reader import (
    init_fridges,
    get_fridge_ids,
    get_fridge_instance,
    get_current_data
)

class TestFridgeReader(unittest.TestCase):
    def setUp(self):
        """Initialize fridges before each test"""
        init_fridges()
    
    def test_fridge_initialization(self):
        """Test that fridges are properly initialized"""
        fridge_ids = get_fridge_ids()
        self.assertEqual(len(fridge_ids), 2)  # We expect 2 fridges
        self.assertIn("fridge_1", fridge_ids)
        self.assertIn("fridge_2", fridge_ids)
    
    def test_get_fridge_instance(self):
        """Test retrieving fridge instances"""
        fridge = get_fridge_instance("fridge_1")
        self.assertIsNotNone(fridge)
        
        # Test invalid fridge ID
        with self.assertRaises(KeyError):
            get_fridge_instance("non_existent_fridge")
    
    def test_get_current_data(self):
        """Test getting current data from fridges"""
        data = get_current_data("fridge_1")
        
        # Check required fields exist
        required_fields = ["fridge_id", "timestamp", "channels", 
                         "sensor_status", "last_pressures_mbar", 
                         "state_message"]
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check specific values
        self.assertEqual(data["fridge_id"], "fridge_1")
        self.assertIsInstance(data["channels"], dict)
        self.assertIsInstance(data["sensor_status"], dict)
        self.assertIsInstance(data["last_pressures_mbar"], list)
        self.assertIsInstance(data["state_message"], str)

if __name__ == "__main__":
    unittest.main()