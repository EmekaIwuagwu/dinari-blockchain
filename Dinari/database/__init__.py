"""
Dinari Database Package
======================
Database storage and management for DinariBlockchain
"""

# Import only the database classes, NOT blockchain classes
from .leveldb_storage import DinariLevelDB

# Package metadata
__version__ = "1.0.0"
__description__ = "Database storage layer for DinariBlockchain"

# Export main database classes
__all__ = [
    'DinariLevelDB',
]

# Note: DO NOT import blockchain classes here to avoid circular imports
# The blockchain module should import from database, not the other way around