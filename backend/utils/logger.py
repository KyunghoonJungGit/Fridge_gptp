"""
@description
A basic logging utility for the fridge monitoring system.

Key features:
- Initializes and configures Python's built-in logging
- Exposes a function to retrieve a named logger

@dependencies
- Python's standard `logging` library

@notes
- Other backend modules can import `get_logger` to emit logs under a shared configuration
- Logging level defaults to INFO but can be adjusted as needed
"""

import logging

# Configure the root logger only once, setting a basic format and INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Retrieve a logger with the given name, using the shared logging configuration.

    :param name: The logger name (usually the calling module's __name__)
    :return: A logger instance
    """
    return logging.getLogger(name)
