"""ID generation module for contextgit.

This module provides functionality for generating sequential node IDs with
type-specific prefixes (e.g., BR-001, SR-012, AR-005).
"""

from .generator import IDGenerator

__all__ = ['IDGenerator']
