"""Checksum calculation module for contextgit.

This module provides functionality for calculating and comparing SHA-256 checksums
of requirement content to detect changes and maintain traceability sync status.
"""

from .calculator import ChecksumCalculator

__all__ = ['ChecksumCalculator']
