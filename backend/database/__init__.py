"""
Database package for logistics data extraction application.
"""

from .manager import DatabaseManager, get_db_manager

__all__ = ['DatabaseManager', 'get_db_manager']
