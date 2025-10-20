"""
Extension methods for the Database class to maintain compatibility with older code.
"""

import logging
from src.models.database import Database

logger = logging.getLogger(__name__)

# Add compatibility methods to Database class
def close(self):
    """
    Compatibility method for closing database connections.
    In the updated architecture, connections are automatically closed
    by the context manager in get_connection.
    """
    # Nothing to do as connections are managed by get_connection
    logger.debug("Database close method called (no-op)")
    pass

def ensure_connection(self):
    """
    Compatibility method for ensuring database connection.
    In the updated architecture, connections are created as needed
    by the context manager in get_connection.
    """
    # Nothing to do as connections are created on demand
    logger.debug("Database ensure_connection method called (no-op)")
    pass

def connection(self):
    """
    Compatibility method for providing database connection.
    Returns the same context manager as get_connection for backward compatibility.
    
    Returns:
        Context manager for database connection
    """
    logger.debug("Using legacy connection() method, consider migrating to get_connection()")
    return self.get_connection()

# Extend the Database class with compatibility methods
Database.close = close
Database.ensure_connection = ensure_connection
Database.connection = connection