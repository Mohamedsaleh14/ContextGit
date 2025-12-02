"""Index domain module for contextgit.

This module provides the IndexManager for CRUD operations on the requirements
index with atomic write guarantees.
"""

from .manager import IndexManager

__all__ = ['IndexManager']
