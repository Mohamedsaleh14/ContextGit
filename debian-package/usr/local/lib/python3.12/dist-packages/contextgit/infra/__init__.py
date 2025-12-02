"""Infrastructure layer for contextgit.

This module provides low-level infrastructure components:
- File system operations
- YAML serialization
- Output formatting
"""

from .filesystem import FileSystem
from .yaml_io import YAMLSerializer
from .output import OutputFormatter

__all__ = ['FileSystem', 'YAMLSerializer', 'OutputFormatter']
