"""
@description
Utility for loading YAML configuration files into Python dictionaries.

Key features:
- load_yaml_config(file_path): reads a YAML file and returns the contents as a Python dict

@dependencies
- PyYAML: for parsing YAML
- Python's logging library (if we choose to log errors)

@notes
- In case the file is missing or invalid, the function returns an empty dict and logs a warning.
- Extend or modify for environment-based overrides if desired.
"""

import os
import yaml
import logging
from typing import Any, Dict

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents as a dictionary.

    :param file_path: The path to the YAML file.
    :return: A dictionary representing the YAML contents. Empty dict if file not found or invalid.
    """
    if not os.path.isfile(file_path):
        logging.warning(f"[config_loader] YAML config file not found: {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                data = {}
            return data
    except Exception as e:
        logging.error(f"[config_loader] Error loading YAML file '{file_path}': {e}")
        return {}
