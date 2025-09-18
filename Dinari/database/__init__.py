"""
Database package for Dinari Blockchain
File: dinari/database/__init__.py
"""

from .leveldb_adapter import DinariLevelDB

__all__ = ['DinariLevelDB']